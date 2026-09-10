# -*- coding: utf-8 -*-
"""
Create Manufacturing Orders from Delivery Orders.

Flow:
1. User clicks "Create Manufacturing Order" on an outgoing delivery.
2. Create child (component) MOs first (bottom-up), then the parent MO.
3. Origin on all MOs = Sale Order reference (fallback: delivery name).
4. Link parent/child via parent_mo_id and production_group parent/child.
5. Purchase RFQs are created later from the MO via "Create Purchase Order".
6. Validate delivery only after linked MOs are done.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import float_round, html2plaintext


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

    def _mrp_custom_sale_origin(self):
        """Sale Order name for MO origin; fallback to delivery name."""
        self.ensure_one()
        sale = self.sale_id if 'sale_id' in self._fields else False
        if sale:
            return sale.name
        return self.name

    def action_create_manufacturing_orders(self):
        """Create MO(s) for finished goods on this delivery (with nested BoMs)."""
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
        origin = self._mrp_custom_sale_origin()
        moves = self.move_ids.filtered(
            lambda m: m.state != 'cancel' and m.product_uom_qty > 0
        )
        for move in moves:
            bom = self._mrp_custom_find_bom(move.product_id)
            if not bom:
                continue
            # Bottom-up: children first, then parent
            mos, _root = self._mrp_custom_create_mo_tree(
                product=move.product_id,
                qty=move.product_uom_qty,
                uom=move.product_uom,
                bom=bom,
                move_dest=move,
                origin=origin,
            )
            created |= mos

        if not created:
            raise UserError(_(
                'No product on this delivery has a Manufacturing Bill of Materials.'
            ))

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

    def _mrp_custom_component_specs(self, product, qty, uom, bom):
        """
        Return list of (component_product, component_qty, component_uom, component_bom)
        for BoM lines that themselves have a normal manufacturing BoM.
        """
        self.ensure_one()
        product_qty = uom._compute_quantity(qty, bom.product_uom_id)
        factor = product_qty / bom.product_qty if bom.product_qty else 0.0
        specs = []
        for line in bom.bom_line_ids:
            if line._skip_bom_line(product):
                continue
            child_bom = self._mrp_custom_find_bom(line.product_id)
            if not child_bom:
                continue
            line_qty = float_round(
                line.product_qty * factor,
                precision_rounding=line.product_uom_id.rounding,
            )
            if line_qty <= 0:
                continue
            specs.append((line.product_id, line_qty, line.product_uom_id, child_bom))
        return specs

    def _mrp_custom_create_mo_tree(self, product, qty, uom, bom, move_dest=False, origin=False):
        """
        Create child component MOs first (recursively), then this MO.

        :return: (all_created_mos, root_mo)
        """
        self.ensure_one()
        origin = origin or self._mrp_custom_sale_origin()
        created = self.env['mrp.production']

        # 1) Create deepest children first (no move_dest yet)
        pending_children = self.env['mrp.production']
        for comp_product, comp_qty, comp_uom, child_bom in self._mrp_custom_component_specs(
            product, qty, uom, bom
        ):
            child_mos, child_root = self._mrp_custom_create_mo_tree(
                product=comp_product,
                qty=comp_qty,
                uom=comp_uom,
                bom=child_bom,
                move_dest=False,
                origin=origin,
            )
            created |= child_mos
            pending_children |= child_root

        # 2) Create this (parent) MO
        mo = self._mrp_custom_create_mo(
            product=product,
            qty=qty,
            uom=uom,
            bom=bom,
            move_dest=move_dest,
            origin=origin,
        )
        created |= mo

        # 3) Link children to this MO (moves + parent_mo + production group)
        for child in pending_children:
            self._mrp_custom_link_child_to_parent(child, mo)

        return created, mo

    def _mrp_custom_link_child_to_parent(self, child_mo, parent_mo):
        """Wire child finished output into parent raw move + Source/Child links."""
        self.ensure_one()
        child_mo.ensure_one()
        parent_mo.ensure_one()

        child_mo.parent_mo_id = parent_mo.id
        child_mo._mrp_custom_link_production_groups(parent_mo)

        raw_move = parent_mo.move_raw_ids.filtered(
            lambda m: m.product_id == child_mo.product_id and m.state != 'cancel'
        )[:1]
        if not raw_move:
            return

        finished = child_mo.move_finished_ids.filtered(
            lambda m: m.product_id == child_mo.product_id and m.state != 'cancel'
        )
        if finished:
            raw_move.write({
                'procure_method': 'make_to_order',
                'move_orig_ids': [Command.link(f.id) for f in finished],
            })
            finished.write({
                'move_dest_ids': [Command.link(raw_move.id)],
            })

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
            'origin': origin or self._mrp_custom_sale_origin(),
            'delivery_picking_id': self.id,
            'company_id': self.company_id.id,
            'picking_type_id': picking_type.id,
            'location_src_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'delivery_instruction': self._mrp_custom_get_delivery_instruction(move_dest),
        }
        if self.company_id.business_unit == 'pg_marine':
            if getattr(self, 'vessel_no_id', False):
                vals['vessel_no_id'] = self.vessel_no_id.id
            if getattr(self, 'imo_number', False):
                vals['imo_number'] = self.imo_number
            if getattr(self, 'port_master_id', False):
                vals['port_master_id'] = self.port_master_id.id
            if getattr(self, 'country_port_id', False):
                vals['country_port_id'] = self.country_port_id.id
        if move_dest:
            vals['move_dest_ids'] = [Command.link(move_dest.id)]

        mo = self.env['mrp.production'].create(vals)

        # Confirm only when MO approval flow is not blocking (or already approved).
        # Pass skip_mrp_approval_check=True so child MOs (which start at
        # pending_qc) can be confirmed here without raising a UserError.
        if 'mo_approval_state' not in mo._fields or mo.mo_approval_state == 'approved':
            mo.with_context(skip_mrp_approval_check=True).action_confirm()

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

    def action_view_mrp_productions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('mrp.mrp_production_action')
        mos = self.mrp_production_ids.filtered(lambda m: m.state != 'cancel')
        action['domain'] = [('id', 'in', mos.ids)]
        action['context'] = {
            'default_delivery_picking_id': self.id,
            'default_origin': self._mrp_custom_sale_origin(),
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
            'default_origin': self._mrp_custom_sale_origin(),
        }
        if len(orders) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = orders.id
        return action

    def button_validate(self):
        """Block validate on OUTGOING deliveries until linked Manufacturing Orders are done.

        Incoming receipts (e.g. from POs generated from MOs) are not blocked
        so they can be validated freely even if MOs are still in progress.
        """
        for picking in self:
            # Only enforce the check on outgoing delivery orders linked to MOs.
            if picking.picking_type_code != 'outgoing':
                continue
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
