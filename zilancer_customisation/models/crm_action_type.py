# -*- coding: utf-8 -*-
from odoo import models, fields


class CRMActionType(models.Model):
    _name = 'crm.action.type'
    _description = 'CRM Action Type'

    name = fields.Char(string="Action Type Name", required=True)
