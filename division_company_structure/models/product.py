from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    division_id = fields.Many2one(
        'division.master',
        string='Division',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        default=lambda self: self.env.user._default_division_id(),
    )

    @api.onchange('company_id')
    def _onchange_company_id_division(self):
        for product in self:
            if product.company_id:
                if not product.division_id or product.division_id.company_id != product.company_id:
                    product.division_id = self.env.user._default_division_id(product.company_id)
            elif product.division_id and product.division_id.company_id \
                    and product.division_id.company_id != product.company_id:
                product.division_id = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    division_id = fields.Many2one(
        'division.master',
        string='Division',
        related='product_tmpl_id.division_id',
        store=True,
        readonly=False,
    )

