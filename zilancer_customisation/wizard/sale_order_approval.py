from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderApprovalWizard(models.TransientModel):
    _name = 'sale.order.approval.wizard'
    _description = 'Sale Order Approval Wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    remarks = fields.Text(string="Approval Remarks", required=True)

    def action_confirm_approval(self):
        """ Handles order approval with remarks and validates user permission """
        if not self.env.user.restricted_approver:
            raise UserError("You are not authorized to approve this order. Contact the admin.")

        self.sale_order_id.action_approve_order(self.remarks)
        return {'type': 'ir.actions.act_window_close'}
