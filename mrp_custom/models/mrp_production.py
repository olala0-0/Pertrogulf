# -*- coding: utf-8 -*-
"""
QC gate on Manufacturing Order completion.

Standard quality_mrp only blocks when checks are still 'none' (todo).
This module also blocks Mark as Done when any check is 'fail'.
"""
from odoo import _, fields, models
from odoo.exceptions import UserError


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

    def _compute_purchase_order_count(self):
        for production in self:
            production.purchase_order_count = len(
                production.purchase_order_ids.filtered(lambda p: p.state != 'cancel')
            )

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

    def pre_button_mark_done(self):
        res = super().pre_button_mark_done()
        # If parent already returned a wizard/action, keep it
        if isinstance(res, dict) and res.get('type') in (
            'ir.actions.act_window',
            'ir.actions.client',
        ):
            return res

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
