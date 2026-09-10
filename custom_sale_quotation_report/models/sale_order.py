from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # --- Petrogulf Aviation fields ---
    aircraft_reg_details = fields.Char(string="Aircraft Reg Details")
    aircraft_type = fields.Char(string="Aircraft Type")
    country_of_origin = fields.Many2one("res.country", string="Country of Origin")

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
        text = self.currency_id.amount_to_text(self.amount_total)
        return f"{text} Only" if text else ""

