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
    is_adnoc = fields.Boolean(
        string="ADNOC Toll Blending Layout", default=False,
        help="Print the simplified ADNOC quotation layout instead of the "
             "standard Toll Blending layout.")

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

