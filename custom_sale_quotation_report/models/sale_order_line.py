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

