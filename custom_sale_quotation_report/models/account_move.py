from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_related_sale_order(self):
        """Sale order this invoice's lines were generated from, if any."""
        self.ensure_one()
        return self.invoice_line_ids.sale_line_ids.order_id[:1]

    def _get_related_delivery(self):
        """Outgoing delivery of the related sale order, if any."""
        self.ensure_one()
        sale_order = self._get_related_sale_order()
        if not sale_order:
            return self.env['stock.picking']
        return sale_order.picking_ids.filtered(lambda p: p.picking_type_id.code == 'outgoing')[:1]

    def get_formatted_website(self):
        website = self.company_id.website or ''
        return website.replace('http://', '').replace('https://', '')

