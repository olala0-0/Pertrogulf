from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _is_pg_ajman_scope(self):
        """True if this PO's company is Petro Gulf Ajman or one of its direct branches."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')