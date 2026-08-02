from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # default=0.0 (not required at DB level) so existing product rows upgrade cleanly.
    # UI can still mark these required on the form if needed.
    weight_per_unit = fields.Float(string="Weight per Unit (kg)", default=0.0)
    pds_link = fields.Char(string="PDS Link")
    is_expences = fields.Boolean(string="Is Expences")
    pack_size_id = fields.Many2one('pack.size.master', string='PKG Type')
    moq_pkg_type = fields.Char(string='MOQ PKG Type')
    kgs_per_pkg_type = fields.Float(string="KGS per PKG Type", default=0.0)
    density = fields.Float(string="Density", default=0.0)

    sap_fg_code = fields.Char(string='SAP FG Code')
    hs_code = fields.Char(string='HS Code')
    client_product_code = fields.Char(string='Client Product Code')
    sap_fg_description = fields.Text(string='SAP FG Description')
    client_fg_description = fields.Text(string='Client FG Description')

    height = fields.Float(string="Height (cm)", default=0.0)
    width = fields.Float(string="Width (cm)", default=0.0)
    gross_weight = fields.Float(string="Gross Weight (kg)", default=0.0)
    net_weight = fields.Float(string="Net Weight (kg)", default=0.0)

    # Analysis Codes
    analysis_product_type_id = fields.Many2one(
        'analysis.product.type',
        string='Product Type',
    )
    analysis_brand_id = fields.Many2one(
        'analysis.product.brand',
        string='Brand',
    )
    analysis_product_categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
    )
    analysis_api_id = fields.Many2one(
        'analysis.api.api',
        string='API',
    )
    analysis_sae_id = fields.Many2one(
        'analysis.sae.sae',
        string='SAE',
    )
    analysis_tbn_id = fields.Many2one(
        'analysis.tbn.tbn',
        string='TBN',
    )
    analysis_iso_tbn_id = fields.Many2one(
        'analysis.iso.tbn',
        string='ISO / TBN',
    )
    analysis_package_id = fields.Many2one(
        'uom.uom',
        string='Packaging',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    density = fields.Float(
        related='product_tmpl_id.density',
        string="Density",
        readonly=False,
        store=True,
    )
    # Analysis Codes fields live on product.template and are available on
    # variants via _inherits (product_tmpl_id), including the Analysis Codes tab.
