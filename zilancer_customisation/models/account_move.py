# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_type = fields.Selection(
        [("local_sale", "Local Sales"), ("export", "Export"), ("out_of_scope", "Out of Scope")],
        string="Sale Type",
    )

    @api.onchange('sale_type')
    def _onchange_sale_type_update_lines(self):
        for move in self:
            if move.is_invoice(include_receipts=True):
                move.invoice_line_ids._compute_account_id()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id', 'move_id.sale_type')
    def _compute_account_id(self):
        super()._compute_account_id()
        for line in self:
            if (
                line.display_type == 'product'
                and line.move_id
                and line.move_id.is_sale_document(include_receipts=True)
                and line.move_id.sale_type
                and line.product_id
                and line.product_id.categ_id
            ):
                sale_type_account = line.product_id.categ_id.with_company(line.company_id)._get_sale_type_income_account(line.move_id.sale_type)
                if sale_type_account:
                    if line.move_id.fiscal_position_id:
                        sale_type_account = line.move_id.fiscal_position_id.map_account(sale_type_account)
                    line.account_id = sale_type_account


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _ensure_code_is_unique(self):
        """
        Allow different companies to have separate accounts with the same code (e.g. 10113).
        Enforces code uniqueness strictly within each individual company.
        """
        for account in self.sudo():
            for company in account.company_ids.root_id:
                if not account.with_company(company).code:
                    raise ValidationError(self.env._("The code must be set for every company to which this account belongs."))

        account_ids_to_check_by_company = defaultdict(list)
        for account in self.sudo():
            for company in account.company_ids:
                account_ids_to_check_by_company[company].append(account.id)

        for company, account_ids in account_ids_to_check_by_company.items():
            accounts = self.browse(account_ids).with_prefetch(self.ids).sudo()
            accounts_by_code = accounts.with_company(company).grouped('code')
            duplicate_codes = None
            if len(accounts_by_code) < len(accounts):
                duplicate_codes = [code for code, accs in accounts_by_code.items() if len(accs) > 1]
            elif duplicates := self.with_company(company).sudo().with_context(active_test=False).search_fetch(
                [
                    ('code', 'in', list(accounts_by_code)),
                    ('id', 'not in', self.ids),
                    ('company_ids', 'in', company.ids),
                ],
                ['code_store'],
            ):
                duplicate_codes = duplicates.mapped('code')
            if duplicate_codes:
                raise ValidationError(
                    self.env._("Account codes must be unique per company. Duplicate codes found: %s", ", ".join(duplicate_codes))
                )
