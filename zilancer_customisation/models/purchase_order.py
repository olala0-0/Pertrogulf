# -*- coding: utf-8 -*-

from odoo import models, fields, _


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

    def inter_company_create_sale_order(self, company):
        """Ensure products in PO lines are allowed in target company before creating inter-company SO."""
        for po in self:
            for line in po.order_line:
                product = line.product_id
                if not product:
                    continue
                tmpl = product.product_tmpl_id.sudo()
                if "company_ids" in tmpl._fields:
                    if company not in tmpl.company_ids:
                        tmpl.write({"company_ids": [fields.Command.link(company.id)]})
                elif tmpl.company_id and tmpl.company_id != company:
                    tmpl.write({"company_id": False})

        return super(
            PurchaseOrder,
            self.with_context(skip_check_company=True, inter_company_create=True)
        ).inter_company_create_sale_order(company)

