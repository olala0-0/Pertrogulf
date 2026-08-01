# -*- coding: utf-8 -*-

from odoo import models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """Use business-unit sale order numbering for inter-company SO creation."""
        sale_order_data = super()._prepare_sale_order_data(
            name, partner, company, direct_delivery_address
        )
        business_unit = company.business_unit
        sale_order_data["business_unit"] = business_unit
        sale_order_data["name"] = _("New")
        return sale_order_data
