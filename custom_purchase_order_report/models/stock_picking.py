from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _is_pg_ajman_company(self):
        """True if this picking's company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')

    def _is_pg_ajman_scope(self):
        """True for sale (delivery) pickings whose company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        return bool(self.sale_id) and self._is_pg_ajman_company()

    def _is_pg_ajman_grn_scope(self):
        """True for incoming receipts whose company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        return self.picking_type_id.code == 'incoming' and self._is_pg_ajman_company()