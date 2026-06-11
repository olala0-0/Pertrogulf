# -*- coding: utf-8 -*-
from odoo import models, fields


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    action_point_ids = fields.One2many('crm.action.point', 'crm_lead_id', string="Action Points")
    expected_volume_ltr = fields.Float("Expected Volume (in Ltrs)")
