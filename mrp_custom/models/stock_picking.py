# -*- coding: utf-8 -*-
"""
Create Manufacturing Orders from Delivery Orders.

Flow:
1. User clicks "Create Manufacturing Order" on an outgoing delivery.
2. For each delivery product that has a normal BoM → create MO linked to the
   delivery move (move_dest_ids) so finished qty feeds the delivery.
3. If BoM components also have a normal BoM → create child MOs and link them
   to the parent MO raw moves (dependency chain).
4. For BoM components without a manufacturing BoM → create Purchase RFQs
   (grouped by vendor) linked to the related MOs / delivery.
5. Validate delivery only after linked MOs are done (stock is available).
"""
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import html2plaintext


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_production_ids = fields.One2many(
        'mrp.production',
        'delivery_picking_id',
        string='Manufacturing Orders',
    )
    mrp_production_count = fields.Integer(
        compute='_compute_mrp_production_count',
    )
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'delivery_picking_id',
        string='Purchase RFQs',
    )
    purchase_order_count = fields.Integer(
        compute='_compute_purchase_order_count',
    )

    @api.depends('mrp_production_ids')
    def _compute_mrp_production_count(self):
        for picking in self:
            picking.mrp_production_count = len(
                picking.mrp_production_ids.filtered(lambda m: m.state != 'cancel')
            )

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for picking in self:
            picking.purchase_order_count = len(
                picking.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
            )

    def action_create_manufacturing_orders(self):
        """Create MO(s) for finished goods on this delivery (with nested BoMs + RFQs)."""
        self.ensure_one()
        if self.picking_type_code != 'outgoing':
            raise UserError(_('Manufacturing Orders can only be created from a Delivery Order.'))
        if self.state in ('done', 'cancel'):
            raise UserError(_('You cannot create Manufacturing Orders on a done or cancelled delivery.'))

        existing = self.mrp_production_ids.filtered(lambda m: m.state != 'cancel')
        if existing:
            raise UserError(_(
                'Manufacturing Orders already exist for this delivery:\n%s'
            ) % '\n'.join(existing.mapped('name')))

        created = self.env['mrp.production']
        moves = self.move_ids.filtered(
            lambda m: m.state != 'cancel' and m.product_uom_qty > 0
        )
        for move in moves:
            bom = self._mrp_custom_find_bom(move.product_id)
            if not bom:
                continue
            mo = self._mrp_custom_create_mo(
                product=move.product_id,
                qty=move.product_uom_qty,
                uom=move.product_uom,
                bom=bom,
                move_dest=move,
                origin=self.name,
            )
            created |= mo
            # Nested finished goods (components that also have a BoM)
            created |= self._mrp_custom_create_component_mos(mo)

        if not created:
            raise UserError(_(
                'No product on this delivery has a Manufacturing Bill of Materials.'
            ))

        # Purchase RFQs for BoM components that are not manufactured
        self._mrp_custom_create_purchase_rfqs(created)

        # Try to reserve delivery once MOs are linked
        self.action_assign()
        return self.action_view_mrp_productions()

    def _mrp_custom_find_bom(self, product):
        """Return normal BoM for product, or empty recordset."""
        return self.env['mrp.bom']._bom_find(
            product,
            company_id=self.company_id.id,
            bom_type='normal',
        ).get(product)

    def _mrp_custom_get_delivery_instruction(self, move_dest=False):
        """
        Delivery Order instruction text to copy onto the Manufacturing Order.
        Priority: picking Note, then SO special delivery instructions,
        then line Dispatch Instructions.
        """
        self.ensure_one()
        parts = []
        if self.note:
            note_text = html2plaintext(self.note).strip()
            if note_text:
                parts.append(note_text)
        sale = self.sale_id if 'sale_id' in self._fields else False
        if sale and sale.delivery_special_instructions:
            special = html2plaintext(sale.delivery_special_instructions).strip()
            if special:
                parts.append(special)
        if move_dest and move_dest.remarks:
            parts.append(move_dest.remarks)
        seen = set()
        unique_parts = []
        for part in parts:
            key = part.strip()
            if key and key not in seen:
                seen.add(key)
                unique_parts.append(key)
        return '\n\n'.join(unique_parts) or False

    def _mrp_custom_create_mo(self, product, qty, uom, bom, move_dest=False, origin=False):
        """Create one MO; optionally link finished output to move_dest."""
        self.ensure_one()
        product_qty = uom._compute_quantity(qty, bom.product_uom_id)
        warehouse = self.picking_type_id.warehouse_id
        picking_type = bom.picking_type_id or warehouse.manu_type_id
        if not picking_type:
            raise UserError(_(
                'No Manufacturing Operation Type found for warehouse %s.'
            ) % (warehouse.display_name,))

        vals = {
            'product_id': product.id,
            'product_qty': product_qty,
            'product_uom_id': bom.product_uom_id.id,
            'bom_id': bom.id,
            'origin': origin or self.name,
            'delivery_picking_id': self.id,
            'company_id': self.company_id.id,
            'picking_type_id': picking_type.id,
            'location_src_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'delivery_instruction': self._mrp_custom_get_delivery_instruction(move_dest),
        }
        if move_dest:
            vals['move_dest_ids'] = [Command.link(move_dest.id)]

        mo = self.env['mrp.production'].create(vals)

        # Confirm only when MO approval flow is not blocking (or already approved)
        if 'mo_approval_state' not in mo._fields or mo.mo_approval_state == 'approved':
            mo.action_confirm()

        # Ensure destination move waits for this production (MTO link)
        if move_dest:
            finished = mo.move_finished_ids.filtered(
                lambda m: m.product_id == product and m.state != 'cancel'
            )
            if finished:
                move_dest.write({
                    'procure_method': 'make_to_order',
                    'move_orig_ids': [Command.link(f.id) for f in finished],
                })
        return mo

    def _mrp_custom_create_component_mos(self, parent_mo):
        """
        For each raw component of parent_mo that has its own BoM,
        create a child MO and link it to the parent raw move.
        """
        self.ensure_one()
        created = self.env['mrp.production']
        for raw_move in parent_mo.move_raw_ids.filtered(lambda m: m.state != 'cancel'):
            bom = self._mrp_custom_find_bom(raw_move.product_id)
            if not bom:
                continue
            child = self._mrp_custom_create_mo(
                product=raw_move.product_id,
                qty=raw_move.product_uom_qty,
                uom=raw_move.product_uom,
                bom=bom,
                move_dest=raw_move,
                origin=parent_mo.name,
            )
            child.parent_mo_id = parent_mo.id
            created |= child
            # Recurse if child components are also manufactured
            created |= self._mrp_custom_create_component_mos(child)
        return created

    def _mrp_custom_create_purchase_rfqs(self, productions):
        """
        Create draft Purchase RFQs for BoM components that do not have a
        manufacturing BoM (i.e. must be purchased), grouped by vendor.
        RFQs are linked to the delivery and related MOs.
        """
        self.ensure_one()
        # product_id -> {qty in product uom, uom, mo_ids, bom_ids}
        to_buy = defaultdict(lambda: {
            'qty': 0.0,
            'uom': False,
            'mo_ids': self.env['mrp.production'],
            'bom_ids': self.env['mrp.bom'],
        })

        for mo in productions:
            for raw_move in mo.move_raw_ids.filtered(
                lambda m: m.state != 'cancel' and m.product_uom_qty > 0
            ):
                # Skip components that are manufactured via a child MO
                if self._mrp_custom_find_bom(raw_move.product_id):
                    continue
                product = raw_move.product_id
                qty = raw_move.product_uom._compute_quantity(
                    raw_move.product_uom_qty, product.uom_id
                )
                entry = to_buy[product.id]
                entry['qty'] += qty
                entry['uom'] = product.uom_id
                entry['mo_ids'] |= mo
                if mo.bom_id:
                    entry['bom_ids'] |= mo.bom_id

        if not to_buy:
            return self.env['purchase.order']

        # Group lines by vendor
        vendor_lines = defaultdict(list)
        missing_vendor = []
        for product_id, data in to_buy.items():
            product = self.env['product.product'].browse(product_id)
            seller = product._select_seller(
                quantity=data['qty'],
                uom_id=data['uom'],
            )
            partner = seller.partner_id if seller else False
            if not partner and product.seller_ids:
                partner = product.seller_ids[0].partner_id
            if not partner:
                missing_vendor.append(product.display_name)
                continue
            vendor_lines[partner.id].append({
                'product': product,
                'qty': data['qty'],
                'uom': data['uom'],
                'mo_ids': data['mo_ids'],
                'bom_ids': data['bom_ids'],
                'seller': seller,
            })

        if missing_vendor:
            raise UserError(_(
                'Cannot create Purchase RFQs. Set a Vendor on these products:\n%s'
            ) % '\n'.join(missing_vendor))

        PurchaseOrder = self.env['purchase.order']
        created_pos = PurchaseOrder
        date_planned = fields.Datetime.now()

        for partner_id, lines in vendor_lines.items():
            mo_ids = self.env['mrp.production']
            bom_names = set()
            for line in lines:
                mo_ids |= line['mo_ids']
                bom_names.update(line['bom_ids'].mapped('display_name'))

            origin_parts = [self.name] + mo_ids.mapped('name')
            po = PurchaseOrder.create({
                'partner_id': partner_id,
                'origin': ', '.join(origin_parts),
                'company_id': self.company_id.id,
                'delivery_picking_id': self.id,
                'mrp_production_ids': [Command.set(mo_ids.ids)],
                'order_line': [
                    Command.create({
                        'product_id': line['product'].id,
                        'product_qty': line['qty'],
                        'product_uom_id': line['uom'].id,
                        'date_planned': date_planned,
                        'name': _(
                            '%(product)s (MO: %(mos)s%(bom)s)'
                        ) % {
                            'product': line['product'].display_name,
                            'mos': ', '.join(line['mo_ids'].mapped('name')),
                            'bom': (
                                _(' / BoM: %s') % ', '.join(line['bom_ids'].mapped('display_name'))
                                if line['bom_ids'] else ''
                            ),
                        },
                    })
                    for line in lines
                ],
            })
            created_pos |= po
            po.message_post(body=_(
                'RFQ created from Delivery %(picking)s for Manufacturing Orders: %(mos)s'
            ) % {
                'picking': self.name,
                'mos': ', '.join(mo_ids.mapped('name')),
            })

        if created_pos:
            self.message_post(body=_(
                'Purchase RFQs created: %(rfqs)s'
            ) % {'rfqs': ', '.join(created_pos.mapped('name'))})

        return created_pos

    def action_view_mrp_productions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('mrp.mrp_production_action')
        mos = self.mrp_production_ids.filtered(lambda m: m.state != 'cancel')
        action['domain'] = [('id', 'in', mos.ids)]
        action['context'] = {
            'default_delivery_picking_id': self.id,
            'default_origin': self.name,
        }
        if len(mos) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = mos.id
        return action

    def action_view_purchase_orders(self):
        self.ensure_one()
        orders = self.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        action['domain'] = [('id', 'in', orders.ids)]
        action['context'] = {
            'default_delivery_picking_id': self.id,
            'default_origin': self.name,
        }
        if len(orders) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = orders.id
        return action

    def button_validate(self):
        """Block validate until linked Manufacturing Orders are done."""
        for picking in self:
            pending = picking.mrp_production_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
            )
            if pending:
                raise UserError(_(
                    'Cannot validate delivery %(picking)s.\n'
                    'Complete these Manufacturing Orders first:\n%(mos)s'
                ) % {
                    'picking': picking.name,
                    'mos': '\n'.join(pending.mapped('name')),
                })
        return super().button_validate()
