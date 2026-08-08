# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    vessel_no_id = fields.Many2one("vessel.no", string="Vessel Name")
    imo_number = fields.Char(string="IMO No")
    port_master_id = fields.Many2one("port.master", string="Port of Delivery")
    country_port_id = fields.Many2one("res.country", string="Country - linked to the Port")
    incoterm_id = fields.Many2one("account.incoterms", string="Delivery Terms")
    business_unit = fields.Selection(related="company_id.business_unit", string="Business Unit", readonly=True)

    @api.onchange("vessel_no_id")
    def _onchange_vessel_no_id(self):
        if self.vessel_no_id and self.vessel_no_id.imo_number:
            self.imo_number = self.vessel_no_id.imo_number

    @api.onchange("port_master_id")
    def _onchange_port_master_id(self):
        if self.port_master_id:
            self.country_port_id = self.port_master_id.country_id.id

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


