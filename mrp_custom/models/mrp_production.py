# -*- coding: utf-8 -*-
"""
QC gate on Manufacturing Order completion + Create Purchase Order (RFQs)
from MO components + QC Controls from BoM.
"""
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    delivery_picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        index=True,
        copy=False,
        help='Delivery Order that created this Manufacturing Order.',
    )
    delivery_instruction = fields.Text(
        string='Delivery Instruction',
        copy=False,
        help='Copied from the Delivery Order note / sale delivery instructions '
             'when the MO is created from the delivery.',
    )
    parent_mo_id = fields.Many2one(
        'mrp.production',
        string='Parent MO',
        index=True,
        copy=False,
        help='Parent Manufacturing Order that needs this product as a component.',
    )
    child_mo_ids = fields.One2many(
        'mrp.production',
        'parent_mo_id',
        string='Component MOs',
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'purchase_order_mrp_production_rel',
        'production_id',
        'purchase_order_id',
        string='Purchase RFQs',
        copy=False,
    )
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    qc_control_ids = fields.One2many(
        'mrp.production.qc.control',
        'production_id',
        string='QC Controls',
        copy=False,
    )
    qc_controls_readonly = fields.Boolean(
        compute='_compute_qc_controls_readonly',
        string='QC Controls Readonly',
    )

    @api.depends('state')
    def _compute_qc_controls_readonly(self):
        for production in self:
            production.qc_controls_readonly = production.state == 'done'

    @api.depends('purchase_order_ids', 'purchase_order_ids.state')
    def _compute_purchase_order_count(self):
        for production in self:
            production.purchase_order_count = len(
                production.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
            )

    @api.onchange('bom_id')
    def _onchange_bom_id_qc_controls(self):
        if not self.bom_id:
            self.qc_control_ids = [Command.clear()]
            return
        self.qc_control_ids = [Command.clear()] + [
            Command.create({
                'name': line.name,
                'sequence': line.sequence,
            })
            for line in self.bom_id.qc_control_ids.filtered(
                lambda l: l.name and str(l.name).strip()
            )
        ]

    @api.model
    def _mrp_custom_sanitize_qc_control_commands(self, commands):
        """Drop CREATE commands without a name (editable-list phantom rows)."""
        if not commands:
            return commands
        cleaned = []
        for command in commands:
            if not command:
                continue
            cmd = command[0]
            if cmd in (Command.CREATE, 0):
                vals = command[2] or {}
                name = vals.get('name')
                if not name or not str(name).strip():
                    continue
            cleaned.append(command)
        return cleaned

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('qc_control_ids'):
                vals['qc_control_ids'] = self._mrp_custom_sanitize_qc_control_commands(
                    vals['qc_control_ids']
                )
        productions = super().create(vals_list)
        for production in productions:
            if production.bom_id and not production.qc_control_ids:
                production._mrp_custom_sync_qc_controls_from_bom()
        return productions

    def write(self, vals):
        vals = dict(vals)
        if vals.get('qc_control_ids'):
            vals['qc_control_ids'] = self._mrp_custom_sanitize_qc_control_commands(
                vals['qc_control_ids']
            )
        bom_changed = 'bom_id' in vals
        res = super().write(vals)
        if bom_changed:
            for production in self.filtered(lambda p: p.state != 'done'):
                production._mrp_custom_sync_qc_controls_from_bom()
        return res

    def _mrp_custom_sync_qc_controls_from_bom(self):
        """Replace MO QC Controls with those defined on the BoM / Blend Sheet."""
        QcControl = self.env['mrp.production.qc.control']
        for production in self:
            production.qc_control_ids.unlink()
            if not production.bom_id:
                continue
            lines = production.bom_id.qc_control_ids.filtered(
                lambda l: l.name and str(l.name).strip()
            )
            if not lines:
                continue
            QcControl.create([
                {
                    'production_id': production.id,
                    'name': line.name,
                    'sequence': line.sequence,
                }
                for line in lines
            ])

    @api.depends(
        'production_group_id.child_ids.production_ids',
        'child_mo_ids',
        'child_mo_ids.state',
    )
    def _compute_mrp_production_child_count(self):
        for production in self:
            production.mrp_production_child_count = len(production._get_children())

    @api.depends(
        'production_group_id.parent_ids.production_ids',
        'parent_mo_id',
        'parent_mo_id.state',
    )
    def _compute_mrp_production_source_count(self):
        for production in self:
            production.mrp_production_source_count = len(production._get_sources())

    def _get_children(self):
        """Include custom component MOs when production-group link is missing."""
        children = super()._get_children()
        return children | self.child_mo_ids.filtered(lambda m: m.state != 'cancel')

    def _get_sources(self):
        """Include custom parent MO when production-group link is missing."""
        sources = super()._get_sources()
        if self.parent_mo_id and self.parent_mo_id.state != 'cancel':
            sources |= self.parent_mo_id
        return sources

    def _mrp_custom_link_production_groups(self, parent_mo):
        """Link this MO as a child of parent_mo for Source/Child smart buttons."""
        self.ensure_one()
        parent_mo.ensure_one()
        if not self.production_group_id or not parent_mo.production_group_id:
            return
        self.production_group_id.parent_ids = [
            Command.link(parent_mo.production_group_id.id)
        ]

    def _mrp_custom_all_qc_controls_passed(self):
        self.ensure_one()
        lines = self.qc_control_ids
        if not lines:
            return True
        return all(line.result == 'pass' for line in lines)

    def action_view_purchase_orders(self):
        self.ensure_one()
        orders = self.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        action['domain'] = [('id', 'in', orders.ids)]
        action['context'] = {'default_mrp_production_ids': [(6, 0, self.ids)]}
        if len(orders) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = orders.id
        return action

    def action_create_purchase_orders(self):
        """Create Purchase RFQs for this MO's purchase components (and child MOs)."""
        self.ensure_one()
        if self.state in ('cancel', 'done'):
            raise UserError(_(
                'Cannot create Purchase Orders from a done or cancelled Manufacturing Order.'
            ))
        existing = self.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
        if existing:
            raise UserError(_(
                'Purchase RFQs already exist for this Manufacturing Order:\n%s'
            ) % '\n'.join(existing.mapped('name')))

        productions = self._mrp_custom_all_related_mos()
        created = self._mrp_custom_create_purchase_rfqs(productions)
        if not created:
            raise UserError(_(
                'No purchase components found on Manufacturing Order %(mo)s.\n'
                'All components either have a manufacturing BoM or there are no components.'
            ) % {'mo': self.name})
        return self.action_view_purchase_orders()

    def _mrp_custom_all_related_mos(self):
        """This MO plus all nested child component MOs."""
        self.ensure_one()
        mos = self.browse(self.id)
        children = self.child_mo_ids.filtered(lambda m: m.state != 'cancel')
        while children:
            mos |= children
            children = children.mapped('child_mo_ids').filtered(
                lambda m: m.state != 'cancel' and m not in mos
            )
        return mos

    def _mrp_custom_find_bom(self, product):
        """Return normal BoM for product, or empty recordset."""
        return self.env['mrp.bom']._bom_find(
            product,
            company_id=self.company_id.id,
            bom_type='normal',
        ).get(product)

    def _mrp_custom_create_purchase_rfqs(self, productions):
        """
        Create draft Purchase RFQs for BoM components that do not have a
        manufacturing BoM (i.e. must be purchased), grouped by vendor.
        """
        self.ensure_one()
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
                # Skip components that are manufactured via a child MO / own BoM
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
        delivery = self.delivery_picking_id

        for partner_id, lines in vendor_lines.items():
            mo_ids = self.env['mrp.production']
            for line in lines:
                mo_ids |= line['mo_ids']

            origin_parts = ([delivery.name] if delivery else []) + mo_ids.mapped('name')
            po_vals = {
                'partner_id': partner_id,
                'origin': ', '.join(origin_parts),
                'company_id': self.company_id.id,
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
            }
            if delivery:
                po_vals['delivery_picking_id'] = delivery.id

            po = PurchaseOrder.create(po_vals)
            created_pos |= po
            po.message_post(body=_(
                'RFQ created from Manufacturing Order %(mo)s.'
            ) % {'mo': self.name})

        if created_pos:
            self.message_post(body=_(
                'Purchase RFQs created: %(rfqs)s'
            ) % {'rfqs': ', '.join(created_pos.mapped('name'))})

        return created_pos

    def _mrp_custom_get_quality_checks(self):
        """All quality checks linked to this MO (including workorder checks)."""
        self.ensure_one()
        QualityCheck = self.env['quality.check']
        domain = [('production_id', '=', self.id)]
        if 'workorder_id' in QualityCheck._fields and self.workorder_ids:
            domain = ['|', ('workorder_id', 'in', self.workorder_ids.ids)] + domain
        return QualityCheck.search(domain)

    def _check_qc_status(self):
        """All quality checks must be done and passed (no 'none' / 'fail')."""
        for production in self:
            for check in production._mrp_custom_get_quality_checks():
                if check.quality_state in ('none', 'fail'):
                    return False
        return True

    def _mrp_custom_check_qc_controls_complete(self):
        """Block Done until every QC Control line is Pass."""
        for production in self:
            lines = production.qc_control_ids
            if not lines:
                continue
            pending = lines.filtered(lambda l: not l.result)
            failed = lines.filtered(lambda l: l.result == 'fail')
            if pending:
                raise UserError(_(
                    'Cannot complete Manufacturing Order %(mo)s.\n'
                    'Set a result (Pass) on all QC Controls first.\n'
                    'Pending: %(controls)s'
                ) % {
                    'mo': production.name,
                    'controls': ', '.join(pending.mapped('name')),
                })
            if failed:
                raise UserError(_(
                    'Cannot complete Manufacturing Order %(mo)s.\n'
                    'All QC Controls must be Pass. Failed controls:\n%(controls)s'
                ) % {
                    'mo': production.name,
                    'controls': '\n'.join(failed.mapped('name')),
                })

    def pre_button_mark_done(self):
        res = super().pre_button_mark_done()
        # If parent already returned a wizard/action, keep it
        if isinstance(res, dict) and res.get('type') in (
            'ir.actions.act_window',
            'ir.actions.client',
        ):
            return res

        self._mrp_custom_check_qc_controls_complete()

        for production in self:
            checks = production._mrp_custom_get_quality_checks()
            todo = checks.filtered(lambda c: c.quality_state == 'none')
            failed = checks.filtered(lambda c: c.quality_state == 'fail')
            if todo:
                raise UserError(_(
                    'You still need to do the quality checks on %(mo)s before completing it.\n'
                    'Pending checks: %(checks)s'
                ) % {
                    'mo': production.name,
                    'checks': ', '.join(
                        todo.mapped(
                            lambda c: c.name or (c.point_id.display_name if c.point_id else _('Quality Check'))
                        )
                    ),
                })
            if failed:
                raise UserError(_(
                    'Cannot complete Manufacturing Order %(mo)s.\n'
                    'The following quality checks failed (all checks must Pass):\n%(checks)s'
                ) % {
                    'mo': production.name,
                    'checks': '\n'.join(
                        failed.mapped(
                            lambda c: c.name or (c.point_id.display_name if c.point_id else _('Quality Check'))
                        )
                    ),
                })
        return res

    def button_mark_done(self):
        self._mrp_custom_check_qc_controls_complete()
        return super().button_mark_done()
