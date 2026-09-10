from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    division_id = fields.Many2one(
        'division.master',
        string='Division',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        default=lambda self: self.env.user._default_division_id(),
    )

    @api.onchange('company_id')
    def _onchange_company_id_division(self):
        for order in self:
            if order.company_id:
                if not order.division_id or order.division_id.company_id != order.company_id:
                    order.division_id = self.env.user._default_division_id(order.company_id)
            elif order.division_id and order.division_id.company_id \
                    and order.division_id.company_id != order.company_id:
                order.division_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id_division(self):
        for order in self:
            if order.partner_id and order.partner_id.division_id:
                company = order.company_id or self.env.company
                if not order.partner_id.division_id.company_id or order.partner_id.division_id.company_id == company:
                    order.division_id = order.partner_id.division_id

