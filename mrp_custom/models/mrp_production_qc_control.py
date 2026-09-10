# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProductionQcControl(models.Model):
    _name = 'mrp.production.qc.control'
    _description = 'Manufacturing Order QC Control'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10)
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    result = fields.Selection(
        [
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ],
        string='Result',
        copy=False,
    )
    description = fields.Text(string='Description')
    is_readonly = fields.Boolean(
        related='production_id.qc_controls_readonly',
        string='Readonly',
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Drop empty phantom lines from editable One2many lists
        vals_list = [
            vals for vals in vals_list
            if vals.get('name') and str(vals.get('name')).strip()
        ]
        if not vals_list:
            return self.browse()
        return super().create(vals_list)

    def action_qc_pass(self):
        for line in self:
            if line.production_id.state == 'done':
                continue
            line.result = 'pass'
        return True

    def action_qc_fail(self):
        for line in self:
            if line.production_id.state == 'done':
                continue
            line.result = 'fail'
        return True
