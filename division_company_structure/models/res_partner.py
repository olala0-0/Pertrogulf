from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    division_id = fields.Many2one(
        'division.master',
        string='Division',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        default=lambda self: self.env.user._default_division_id(),
    )

    @api.onchange('company_id')
    def _onchange_company_id_division(self):
        for partner in self:
            if partner.company_id:
                if not partner.division_id or partner.division_id.company_id != partner.company_id:
                    partner.division_id = self.env.user._default_division_id(partner.company_id)
            elif partner.division_id and partner.division_id.company_id \
                    and partner.division_id.company_id != partner.company_id:
                partner.division_id = False

