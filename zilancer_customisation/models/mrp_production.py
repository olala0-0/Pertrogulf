# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    business_unit = fields.Selection(
        related="company_id.business_unit",
        string="Business Unit",
        readonly=True,
    )
    vessel_no_id = fields.Many2one("vessel.no", string="Vessel Name")
    imo_number = fields.Char(string="IMO Number")
    port_master_id = fields.Many2one("port.master", string="Port Name")
    country_port_id = fields.Many2one("res.country", string="Country of Supply")

    @api.onchange("vessel_no_id")
    def _onchange_vessel_no_id(self):
        if self.vessel_no_id and self.vessel_no_id.imo_number:
            self.imo_number = self.vessel_no_id.imo_number

    @api.onchange("port_master_id")
    def _onchange_port_master_id(self):
        if self.port_master_id:
            self.country_port_id = self.port_master_id.country_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id') or self.env.company.id
            company = self.env['res.company'].browse(company_id)
            if company.business_unit == 'pg_marine':
                # Check delivery picking propagation
                delivery_id = vals.get('delivery_picking_id')
                if delivery_id:
                    picking = self.env['stock.picking'].browse(delivery_id)
                    if not vals.get('vessel_no_id') and getattr(picking, 'vessel_no_id', False):
                        vals['vessel_no_id'] = picking.vessel_no_id.id
                    if not vals.get('imo_number') and getattr(picking, 'imo_number', False):
                        vals['imo_number'] = picking.imo_number
                    if not vals.get('port_master_id') and getattr(picking, 'port_master_id', False):
                        vals['port_master_id'] = picking.port_master_id.id
                    if not vals.get('country_port_id') and getattr(picking, 'country_port_id', False):
                        vals['country_port_id'] = picking.country_port_id.id

                # Check Sale Order origin propagation
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
        return super(MrpProduction, self).create(vals_list)
