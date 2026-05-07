# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2024 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    business_unit = fields.Selection([
        ('pg_marine', 'PG-Marine'),
        ('pg_auto', 'PG-Auto'),
        ('pg_powerx', 'PG-PowerX'),
        ('pg_aviation', 'PG-Aviation'),
        ('pg_tblnd', 'PG-Toll Blending')
    ], string="Business Unit", required=False)
    aviation_logo = fields.Binary(string="PG Aviation Logo")
