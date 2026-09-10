from odoo import api, fields, models


class UserReportHide(models.Model):
    _name = 'user.report.hide'
    _description = 'User Report Hide Configuration'

    model_id = fields.Many2one(
        'ir.model',
        string="Model",
        required=True,
        ondelete='cascade',
        help="Select the model for which you want to hide specific reports."
    )
    report_ids = fields.Many2many(
        'ir.actions.report',
        string="Reports to Hide",
        domain="[('binding_model_id', '=', model_id)]",
        help="Select the specific reports to hide for this model."
    )
    user_id = fields.Many2one(
        'res.users',
        string="User",
        required=True,
        ondelete='cascade'
    )

    @api.onchange('model_id')
    def _onchange_model(self):
        for rec in self:
            rec.report_ids = False
