from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    division_ids = fields.Many2many(
        'division.master',
        'res_company_division_user_rel',
        'user_id',
        'division_id',
        string='Allowed Divisions',
        help='Allowed divisions for this user across companies.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        if any('division_ids' in vals for vals in vals_list):
            self.env.registry.clear_cache()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'division_ids' in vals:
            self.env.registry.clear_cache()
        return res

    def _default_division_id(self, company=None):
        """Default division for a company from the user's allowed divisions."""
        self.ensure_one()
        company = company or self.env.company
        if not self.division_ids:
            return False
        divisions = self.division_ids.filtered(lambda d: not d.company_id or d.company_id == company)
        return divisions[:1].id if divisions else False

    def _get_division_record_domain(self, partner_field=None):
        """Domain used by ir.rule for division & multi-company filtering.

        - Priority 1: Restrict to active company (company_id = False or company_id = active company)
        - Priority 2: If user has allowed divisions for the active company, restrict records ONLY to those divisions.
        """
        self.ensure_one()
        if self.id == 2 or self.has_group('base.group_system'):
            return []

        company = self.env.company
        user_divisions = self.division_ids.filtered(lambda d: not d.company_id or d.company_id == company)

        base_company_domain = ['|', ('company_id', '=', False), ('company_id', '=', company.id)]

        if user_divisions:
            division_domain = [('division_id', 'in', user_divisions.ids)]
            if partner_field:
                division_domain = [
                    '|', ('division_id', 'in', user_divisions.ids),
                    ('%s.division_id' % partner_field, 'in', user_divisions.ids)
                ]
            return base_company_domain + division_domain

        return base_company_domain


