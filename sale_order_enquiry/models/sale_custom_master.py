# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerReferenceMaster(models.Model):
    _name = 'customer.reference.master'
    _description = 'Customer Reference Master'

    name = fields.Char('Inquired Item', required=True)
    customer_brand = fields.Char('Customer Brand')
    cust_ref_pro_category = fields.Char('Cust Ref Product Category')


class BrandMaster(models.Model):
    _name = 'brand.master'
    _description = 'Brand Master'

    name = fields.Char('Brand Name', required=True)
    brand_type = fields.Char('Brand Type', required=True)


class PortMaster(models.Model):
    _name = 'port.master'
    _description = 'Port Master'

    name = fields.Char('Port Name', required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    note = fields.Html('Notes')


class PackSizeMaster(models.Model):
    _name = 'pack.size.master'
    _description = 'Pack Size Master'

    name = fields.Char(string="Pack Size", required=True)
    conversion_factor = fields.Float(string="Conversion Factor", required=True)


class UnitCountMaster(models.Model):
    _name = 'unit.count.master'
    _description = 'No of Units Master'

    name = fields.Integer(string="No of Units", required=True)


class SaleReason(models.Model):
    _name = 'sale.reason'
    _description = 'Sales Reason'

    name = fields.Char(string="Reason", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The reason must be unique!')
    ]

class ProcessStage(models.Model):
    _name = 'process.stage'
    _description = 'Sales Process Stage'

    name = fields.Char(string="Stage Name", required=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Stage name must be unique.')
    ]

class ProcessStage(models.Model):
    _name = 'source.inquiry'
    _description = 'Source of Inquiry'

    name = fields.Char(string="Source of Inquiry", required=True)


class DeliveryBy(models.Model):
    _name = 'delivery.by'
    _description = 'Delivery By'

    name = fields.Char(string="Name", required=True)


class DeliveryType(models.Model):
    _name = 'delivery.type'
    _description = 'Delivery Type'

    name = fields.Char(string="Name", required=True)


class TeamTeam(models.Model):
    _name = 'team.team'
    _description = 'Teams'

    name = fields.Char(string="Name", required=True)


class ProcessMaster(models.Model):
    _name = 'process.master'
    _description = 'Process Master'
    _rec_name = 'team_id'

    name = fields.Integer(string="Sr No")  # Optional: you can also use sequence
    team = fields.Char(string="Team")
    team_id = fields.Many2one('team.team', string="Team", required=True)
    stage_no = fields.Integer(string="Stage No")
    stage = fields.Char(string="Stage")
    progress = fields.Char(string="Progress")
    business_unit = fields.Selection([
        ('automotive', 'Automotive Industrial'),
        ('adnoc', 'ADNOC'),
    ], string="Business Unit")
    color = fields.Integer(string='Color', default=0)


class ProcessUserMaster(models.Model):
    _name = 'process.user.master'
    _description = 'Process User Master'
    _rec_name = 'team_id'

    team_id = fields.Many2one('process.master', string="Team", required="True")
    user_ids = fields.Many2many('res.users', string="Users")
    business_unit = fields.Selection(related="team_id.business_unit", string="Business Unit", store=True)
    user_business_unit = fields.Selection([
        ('automotive', 'Automotive Industrial'),
        ('adnoc', 'ADNOC'),
    ], string="Business Unit")
    portal_master_ids = fields.Many2many('process.master', compute='_compute_portal_master_ids', store=False)

    @api.depends('user_business_unit')
    def _compute_portal_master_ids(self):
        for record in self:
            if record.user_business_unit:
                record.portal_master_ids = self.env['process.master'].search([
                    ('business_unit', '=', record.user_business_unit)]).ids or []
            else:
                record.portal_master_ids = self.env['process.master']


class VesselNo(models.Model):
    _name = 'vessel.no'
    _description = 'Vessel Name'

    name = fields.Char(string="Vessel Name", required=True)
    imo_number = fields.Char(string="IMO")


class IMONumber(models.Model):
    _name = 'imo.number'
    _description = 'IMO Number'

    name = fields.Char(string="Name", required=True)
