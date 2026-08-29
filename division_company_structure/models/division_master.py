from odoo import fields, models


class DivisionMaster(models.Model):
    _name = 'division.master'
    _description = 'Division Master'
    _order = 'name, id'

    name = fields.Char(string='Division Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Parent Company',
        required=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(string='Active', default=True)
