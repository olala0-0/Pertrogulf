# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpBomQcControl(models.Model):
    _name = 'mrp.bom.qc.control'
    _description = 'BoM QC Control Point'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10)
    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Materials',
        required=True,
        ondelete='cascade',
        index=True,
    )
