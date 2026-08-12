from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _is_pg_ajman_scope(self):
        """True if this invoice's company is Petro Gulf Ajman or one of its branch companies."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')

    def _is_pg_powerx_scope(self):
        """True if this invoice's company is Power X or one of its branch companies."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_powerx':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_powerx')

    def _is_tax_invoice_scope(self):
        """The shared Tax Invoice report renders an Ajman or a Power X layout
        (toggled internally by business_unit) - allow either scope."""
        self.ensure_one()
        return self._is_pg_ajman_scope() or self._is_pg_powerx_scope()

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
