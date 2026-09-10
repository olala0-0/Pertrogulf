# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AnalysisMasterMixin(models.AbstractModel):
    _name = 'analysis.master.mixin'
    _description = 'Analysis Master Mixin'
    _order = 'name, id'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, index=True)

    _code_uniq = models.Constraint(
        'unique(code)',
        'Code must be unique!',
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            if record.code and record.name:
                record.display_name = f'[{record.code}] {record.name}'
            else:
                record.display_name = record.name or record.code or ''


class AnalysisProductType(models.Model):
    _name = 'analysis.product.type'
    _description = 'Analysis Product Type'
    _inherit = ['analysis.master.mixin']


class AnalysisProductBrand(models.Model):
    _name = 'analysis.product.brand'
    _description = 'Analysis Product Brand'
    _inherit = ['analysis.master.mixin']


class AnalysisApi(models.Model):
    _name = 'analysis.api.api'
    _description = 'Analysis API'
    _inherit = ['analysis.master.mixin']


class AnalysisSae(models.Model):
    _name = 'analysis.sae.sae'
    _description = 'Analysis SAE'
    _inherit = ['analysis.master.mixin']


class AnalysisTbn(models.Model):
    _name = 'analysis.tbn.tbn'
    _description = 'Analysis TBN'
    _inherit = ['analysis.master.mixin']


class AnalysisIsoTbn(models.Model):
    _name = 'analysis.iso.tbn'
    _description = 'Analysis ISO / TBN'
    _inherit = ['analysis.master.mixin']
