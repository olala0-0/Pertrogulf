from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    restricted_approver = fields.Boolean(string="Restricted from Approval", help="If checked, the user cannot approve sales orders.")



