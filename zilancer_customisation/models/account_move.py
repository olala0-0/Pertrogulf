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

    def _generate_sale_type_invoice_sequence(self):
        self.ensure_one()
        sale_type = self.sale_type or 'local_sale'

        # Map sale_type to sequence prefix and code key
        if sale_type == 'out_of_scope':
            prefix_type = "PGM/OOS/"
            type_code = "out_of_scope"
        elif sale_type == 'export':
            prefix_type = "PGM/E/"
            type_code = "export"
        else:  # local_sale or default
            prefix_type = "PGM/"
            type_code = "local_sale"

        ref_date = self.invoice_date or self.date or fields.Date.context_today(self)
        year_str = ref_date.strftime("%Y")

        sequence_code = f"account.move.sale_type.{type_code}.{year_str}"

        seq = self.env["ir.sequence"].sudo().search([("code", "=", sequence_code)], limit=1)
        if not seq:
            seq_name = f"Invoice Sequence {type_code.replace('_', ' ').title()} {year_str}"
            try:
                seq = self.env["ir.sequence"].sudo().create({
                    "name": seq_name,
                    "code": sequence_code,
                    "prefix": prefix_type,
                    "suffix": f"/{year_str}",
                    "padding": 4,
                    "number_next": 1,
                    "number_increment": 1,
                    "active": True,
                    "implementation": "standard",
                })
                self.env.cr.commit()
            except Exception as e:
                print(f"Error creating sequence {sequence_code}: {e}")

        next_name = False
        try:
            if seq:
                next_name = seq._next()
            if not next_name:
                next_name = self.env["ir.sequence"].sudo().next_by_code(sequence_code)
        except Exception as e:
            print(f"Error fetching sequence for {sequence_code}: {e}")

        if not next_name:
            pattern = f"{prefix_type}%/{year_str}"
            last_move = self.sudo().search(
                [("name", "like", pattern), ("move_type", "in", ["out_invoice", "out_refund"])],
                order="id desc",
                limit=1
            )
            next_num = 1
            if last_move and last_move.name:
                try:
                    parts = last_move.name.split("/")
                    if len(parts) >= 3:
                        num_part = parts[-2]
                        next_num = int(num_part) + 1
                except (ValueError, IndexError):
                    next_num = 1
            next_name = f"{prefix_type}{next_num:04d}/{year_str}"

        return next_name

    def _post(self, soft=True):
        for move in self:
            if move.is_sale_document(include_receipts=True) and (not move.name or move.name == '/' or move.name.startswith('INV/')):
                move.name = move._generate_sale_type_invoice_sequence()
        posted = super()._post(soft=soft)
        for move in posted:
            if move.is_sale_document(include_receipts=True) and (not move.name or move.name == '/' or move.name.startswith('INV/')):
                move.name = move._generate_sale_type_invoice_sequence()
        return posted

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.state == 'posted' and move.is_sale_document(include_receipts=True) and (not move.name or move.name == '/' or move.name.startswith('INV/')):
                move.name = move._generate_sale_type_invoice_sequence()
        return moves


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
