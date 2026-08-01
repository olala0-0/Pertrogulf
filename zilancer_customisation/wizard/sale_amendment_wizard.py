from odoo import api, fields, models
from datetime import date


class SaleOrderAmendmentWizard(models.TransientModel):
    _name = 'sale.order.amendment.wizard'
    _description = 'Sale Order Amendment Wizard'
    
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    remarks = fields.Text(string="Remarks", required=True)
    amendment_reason_id = fields.Many2one("sale.reason", string="Amendment Reason", required=True)
    
    def action_confirm(self):
        """Create amendment record and unlock the sale order"""
        self.ensure_one()
        
        # Create the amendment record
        self.env['amendment.amendment'].create({
            'remarks': self.remarks,
            'amendment_reason_id': self.amendment_reason_id.id,
            'amendment_date': date.today(),
            'user_id': self.env.user.id,
            'sale_id': self.sale_order_id.id,
        })
        
        # Unlock the sale order
        self.sale_order_id.locked = False
        
        return {'type': 'ir.actions.act_window_close'}
