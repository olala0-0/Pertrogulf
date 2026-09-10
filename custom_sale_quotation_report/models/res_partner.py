from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_adnoc = fields.Boolean(
        string="ADNOC Customer", default=False,
        help="Toll Blending quotations for this customer print the "
             "simplified ADNOC layout instead of the standard one.")
