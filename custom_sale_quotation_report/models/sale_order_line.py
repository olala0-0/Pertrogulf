from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # --- Petrogulf Automotive fields ---
    net_weight = fields.Float(string="Net Weight")
    gross_weight = fields.Float(string="Gross Weight")
    pack_type = fields.Char(string="Pack Type")
    hs_code = fields.Char(string="HS Code")

    # --- Power X fields ---
    packing_type = fields.Selection([
        ('drum', 'Drum'),
        ('ibc', 'IBC'),
        ('bulk', 'Bulk'),
        ('flexi', 'Flexi'),
    ], string="Packing Type")
    # Displayed weight label differs by packing_type:
    # Drum -> Net Wt & Gross Wt | IBC -> Gross Wt & Net Wt
    # Bulk -> Net Wt only       | Flexi -> Net Wt only

    # --- Petrogulf Aviation fields ---
    inquired_item = fields.Char(string="Inquired Item")
    offered_product = fields.Char(string="Offered Product")
    category = fields.Char(string="Category")
    lead_time = fields.Char(string="Lead Time")
    pkg_type = fields.Char(string="Pkg Type")
    kgs_per_pkg_type = fields.Float(string="Kgs per Pkg Type")
    total_kgs = fields.Float(string="Total Kgs", compute='_compute_total_kgs', store=True)
    rate_per_pack = fields.Float(string="Rate per Pack")

    # --- Petrogulf Toll Blending fields ---
    selling_unit = fields.Char(string="Selling Unit")
    product_type = fields.Char(string="Product Type")  # used by ADNOC variant

    def _compute_total_kgs(self):
        for line in self:
            line.total_kgs = (line.product_uom_qty or 0.0) * (line.kgs_per_pkg_type or 0.0)
