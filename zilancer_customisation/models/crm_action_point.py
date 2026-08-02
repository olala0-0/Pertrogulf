# -*- coding: utf-8 -*-
from odoo import models, fields


class CRMActionPoint(models.Model):
    _name = 'crm.action.point'
    _description = 'CRM Action Point'

    name = fields.Char(string="Action Name", required=True)
    action_type_id = fields.Many2one('crm.action.type', string="Action Type", required=True)
    remarks = fields.Text(string="Remarks")
    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('wip', 'WIP'),
        ('completed', 'Completed')
    ], string="Status", default="not_started")
    crm_lead_id = fields.Many2one('crm.lead', string="Lead/Opportunity")
