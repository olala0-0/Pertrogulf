# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_report_ids = fields.One2many('user.report.hide', 'user_id', string="Hide Print Reports")

    def write(self, vals):
        res = super().write(vals)
        if 'hide_report_ids' in vals:
            self.env.registry.clear_cache()
        return res
