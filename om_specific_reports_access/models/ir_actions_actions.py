# -*- coding: utf-8 -*-

from odoo import models, tools
from odoo.tools import frozendict


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    @tools.ormcache('model_name', 'self.env.lang')
    def _get_bindings(self, model_name):
        res = super()._get_bindings(model_name)

        hidden_reports = self.env['user.report.hide'].search([
            ('user_id', '=', self.env.user.id),
            ('model_id.model', '=', model_name)
        ])

        if hidden_reports:
            report_ids = hidden_reports.mapped('report_ids').ids
            updated_reports = {
                key: tuple(val for val in value if val['id'] not in report_ids) if key == 'report' else value
                for key, value in res.items()
            }
            return frozendict(updated_reports)

        return res
