from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _is_pg_ajman_scope(self):
        """True for sale (delivery) pickings whose company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        if not self.sale_id:
            return False
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')