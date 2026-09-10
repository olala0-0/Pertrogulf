from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    voucher_no = fields.Char(string="Voucher No")
    buyer_order_no = fields.Char(string="Buyer's Order No")
    other_ref = fields.Char(string="Other References")
    destination = fields.Char(string="Destination")
    despatch_through = fields.Char(string="Despatch Through")
    place_of_supply = fields.Char(string="Place of Supply")
