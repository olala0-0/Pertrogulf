# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    encrypted_name = fields.Char(
        string='Encrypted Name',
        copy=False,
        help='If set, shown as the component name on Bill of Materials / Production Blend Sheet.',
    )

    @api.depends('encrypted_name')
    @api.depends_context('bom_display_encrypted_name')
    def _compute_display_name(self):
        """On BoM / Blend Sheet components, prefer encrypted_name when set."""
        if not self.env.context.get('bom_display_encrypted_name'):
            return super()._compute_display_name()

        with_encrypted = self.filtered(lambda p: bool(p.encrypted_name))
        without_encrypted = self - with_encrypted
        if without_encrypted:
            super(ProductProduct, without_encrypted)._compute_display_name()
        for product in with_encrypted:
            product.display_name = product.encrypted_name

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Allow searching components by encrypted_name on BoM / Blend Sheet."""
        if not self.env.context.get('bom_display_encrypted_name') or not name:
            return super().name_search(name, domain, operator, limit)

        domain = list(domain or [])
        encrypted = self.search(
            domain + [('encrypted_name', operator, name)],
            limit=limit,
        )
        result = [
            (product.id, product.encrypted_name)
            for product in encrypted
        ]
        if limit and len(result) >= limit:
            return result

        remaining = (limit - len(result)) if limit else limit
        others = super().name_search(
            name,
            domain + [('id', 'not in', encrypted.ids)],
            operator,
            remaining,
        )
        return result + others
