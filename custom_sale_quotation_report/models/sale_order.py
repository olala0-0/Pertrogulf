from odoo import models, fields, api

try:
    from num2words import num2words
except ImportError:
    num2words = None


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # --- Petrogulf Aviation fields ---
    aircraft_reg_details = fields.Char(string="Aircraft Reg Details")
    aircraft_type = fields.Char(string="Aircraft Type")
    country_of_origin = fields.Char(string="Country of Origin")

    # --- Petrogulf Toll Blending fields ---
    show_bank_details = fields.Boolean(
        string="Show Bank Details on Quotation", default=False)
    show_vat = fields.Boolean(
        string="Show VAT on Quotation", default=True)
    show_credit_note = fields.Boolean(
        string="Show Discount/Credit Note on Quotation", default=False)

    def _get_amount_in_words(self):
        """Used by Toll Blending report: 'Total Amount in words'."""
        self.ensure_one()
        if not num2words:
            return ""
        try:
            words = num2words(self.amount_total, lang='en').replace('-', ' ')
            return f"{words.title()} {self.currency_id.name} Only"
        except Exception:
            return ""

    # --- Proforma Invoice (Petro Gulf Ajman) ---
    def _is_pg_ajman_scope(self):
        """True if this order's company is Petro Gulf Ajman or one of its branch companies."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')

    # --- Proforma Invoice (Power X) ---
    def _is_pg_powerx_scope(self):
        """True if this order's company is Power X or one of its branch companies."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_powerx':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_powerx')

    # --- Proforma Invoice (Petrogulf Marine) ---
    def _is_pg_marine_scope(self):
        """True if this order's company is Petrogulf Marine or one of its branch companies."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_marine':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_marine')

    def _is_proforma_invoice_scope(self):
        """The shared Proforma Invoice report renders an Ajman/Marine or a
        Power X layout (toggled internally by business_unit) - allow any of
        these scopes."""
        self.ensure_one()
        return self._is_pg_ajman_scope() or self._is_pg_powerx_scope() or self._is_pg_marine_scope()
