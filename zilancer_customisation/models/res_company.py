# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2024 (https://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api
from odoo.addons.sale_order_enquiry.business_unit_data import BUSINESS_UNIT_SELECTION


class ResCompany(models.Model):
    _inherit = 'res.company'

    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        required=False,
    )
    aviation_logo = fields.Binary(string="PG Aviation Logo")
