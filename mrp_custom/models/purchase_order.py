# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    delivery_picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        index=True,
        copy=False,
        help='Delivery Order that triggered Manufacturing Orders and this RFQ.',
    )
    mrp_production_ids = fields.Many2many(
        'mrp.production',
        'purchase_order_mrp_production_rel',
        'purchase_order_id',
        'production_id',
        string='Manufacturing Orders',
        copy=False,
        help='Manufacturing Orders whose BoM components are purchased on this RFQ.',
    )
