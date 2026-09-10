# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    vessel_no_id = fields.Many2one("vessel.no", string="Vessel Name")
    imo_number = fields.Char(string="IMO No")
    port_master_id = fields.Many2one("port.master", string="Port of Delivery")
    country_port_id = fields.Many2one("res.country", string="Country")
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

    def _prepare_picking(self):
        res = super()._prepare_picking()
        if self.company_id.business_unit == 'pg_marine':
            if self.vessel_no_id:
                res['vessel_no_id'] = self.vessel_no_id.id
            if self.imo_number:
                res['imo_number'] = self.imo_number
            if self.port_master_id:
                res['port_master_id'] = self.port_master_id.id
            if self.country_port_id:
                res['country_port_id'] = self.country_port_id.id
        return res

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """Use business-unit sale order numbering for inter-company SO creation."""
        sale_order_data = super()._prepare_sale_order_data(
            name, partner, company, direct_delivery_address
        )
        business_unit = company.business_unit
        sale_order_data["business_unit"] = business_unit
        sale_order_data["name"] = _("New")
        if company.business_unit == 'pg_marine' or self.company_id.business_unit == 'pg_marine':
            if self.vessel_no_id:
                sale_order_data['vessel_no_id'] = self.vessel_no_id.id
            if self.imo_number:
                sale_order_data['imo_number'] = self.imo_number
            if self.port_master_id:
                sale_order_data['port_master_id'] = self.port_master_id.id
            if self.country_port_id:
                sale_order_data['country_port_id'] = self.country_port_id.id
        return sale_order_data

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id') or self.env.company.id
            company = self.env['res.company'].browse(company_id)
            if company.business_unit == 'pg_marine':
                origin = vals.get('origin')
                if origin:
                    sale = self.env['sale.order'].search([('name', '=', origin)], limit=1)
                    if sale:
                        if not vals.get('vessel_no_id') and sale.vessel_no_id:
                            vals['vessel_no_id'] = sale.vessel_no_id.id
                        if not vals.get('imo_number') and sale.imo_number:
                            vals['imo_number'] = sale.imo_number
                        if not vals.get('port_master_id') and sale.port_master_id:
                            vals['port_master_id'] = sale.port_master_id.id
                        if not vals.get('country_port_id') and sale.country_port_id:
                            vals['country_port_id'] = sale.country_port_id.id
        return super().create(vals_list)

    def inter_company_create_sale_order(self, company):
        """Ensure products in PO lines are allowed in target company and pricelist currency matches before creating inter-company SO."""
        intercompany_uid = company.intercompany_user_id.id if company.intercompany_user_id else False
        for po in self:
            if intercompany_uid:
                company_partner = po.company_id.partner_id.sudo()
                pricelist = company_partner.property_product_pricelist
                if pricelist and pricelist.currency_id != po.currency_id:
                    matching_pricelist = self.env['product.pricelist'].sudo().search([
                        ('currency_id', '=', po.currency_id.id),
                        '|', ('company_id', '=', False), ('company_id', '=', company.id),
                    ], limit=1)
                    if not matching_pricelist:
                        matching_pricelist = self.env['product.pricelist'].sudo().create({
                            'name': f"Inter-Company Pricelist ({po.currency_id.name})",
                            'currency_id': po.currency_id.id,
                            'company_id': company.id,
                        })
                    company_partner.write({'property_product_pricelist': matching_pricelist.id})

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



