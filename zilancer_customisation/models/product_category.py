# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_income_local_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Income Account for Local",
        help="This account will be used when validating a customer invoice for Local Sales.",
    )
    property_account_income_export_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Income Account for Export",
        help="This account will be used when validating a customer invoice for Export.",
    )
    property_account_income_out_scope_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Income Account for Out of Scope",
        help="This account will be used when validating a customer invoice for Out of Scope.",
    )
    property_account_income_gcc_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Income Account for GCC",
        help="This account will be used when validating a customer invoice for GCC.",
    )

    def _get_sale_type_income_account(self, sale_type):
        """
        Return the income account for the specified sale_type.
        Traverses parent category hierarchy if not set on the current category.
        Falls back to property_account_income_categ_id if not found.
        """
        self.ensure_one()
        field_map = {
            'local_sale': 'property_account_income_local_categ_id',
            'export': 'property_account_income_export_categ_id',
            'out_of_scope': 'property_account_income_out_scope_categ_id',
            'gcc': 'property_account_income_gcc_categ_id',
        }
        field_name = field_map.get(sale_type)
        if not field_name:
            return self.property_account_income_categ_id

        cat = self
        while cat:
            account = getattr(cat, field_name)
            if account:
                return account
            cat = cat.parent_id

        return self.property_account_income_categ_id
