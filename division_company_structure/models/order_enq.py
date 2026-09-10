from odoo import api, fields, models


class OrderEnq(models.Model):
    _inherit = 'order.enq'

    division_id = fields.Many2one(
        'division.master',
        string='Division',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        default=lambda self: self.env.user._default_division_id(),
    )

    @api.onchange('company_id')
    def _onchange_company_id_division(self):
        for enquiry in self:
            if enquiry.company_id:
                if not enquiry.division_id or enquiry.division_id.company_id != enquiry.company_id:
                    enquiry.division_id = self.env.user._default_division_id(enquiry.company_id)
            elif enquiry.division_id and enquiry.division_id.company_id \
                    and enquiry.division_id.company_id != enquiry.company_id:
                enquiry.division_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id_division(self):
        for enquiry in self:
            if enquiry.partner_id and enquiry.partner_id.division_id:
                company = enquiry.company_id or self.env.company
                if not enquiry.partner_id.division_id.company_id or enquiry.partner_id.division_id.company_id == company:
                    enquiry.division_id = enquiry.partner_id.division_id

