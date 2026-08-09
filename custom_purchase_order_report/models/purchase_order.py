from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    voucher_no = fields.Char(string="Voucher No")
    buyer_order_no = fields.Char(string="Buyer's Order No")
    other_ref = fields.Char(string="Other References")
    destination = fields.Char(string="Destination")
    despatch_through = fields.Char(string="Despatch Through")
    place_of_supply = fields.Char(string="Place of Supply")

    def _is_pg_ajman_scope(self):
        """True if this PO's company is Petro Gulf Ajman or one of its direct branches."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')