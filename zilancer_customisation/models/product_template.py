from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    weight_per_unit = fields.Float(string="Weight per Unit (kg)", required=True)
    pds_link = fields.Char(string="PDS Link")
    is_expences = fields.Boolean(string="Is Expences")
    pack_size_id = fields.Many2one('pack.size.master', string='PKG Type')
    moq_pkg_type = fields.Char(string='MOQ PKG Type')
    kgs_per_pkg_type = fields.Float(string="KGS per PKG Type")

    sap_fg_code = fields.Char(string='SAP FG Code')
    hs_code = fields.Char(string='HS Code')
    client_product_code = fields.Char(string='Client Product Code')
    sap_fg_description = fields.Text(string='SAP FG Description')
    client_fg_description = fields.Text(string='Client FG Description')
