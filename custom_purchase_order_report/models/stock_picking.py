from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _is_pg_ajman_company(self):
        """True if this picking's company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_ajman':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_ajman')

    def _is_pg_ajman_scope(self):
        """True for sale (delivery) pickings whose company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        return bool(self.sale_id) and self._is_pg_ajman_company()

    def _is_pg_ajman_grn_scope(self):
        """True for incoming receipts whose company is Petro Gulf Ajman or a direct branch."""
        self.ensure_one()
        return self.picking_type_id.code == 'incoming' and self._is_pg_ajman_company()

    def _is_pg_powerx_company(self):
        """True if this picking's company is Power X or a direct branch."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_powerx':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_powerx')

    def _is_pg_marine_company(self):
        """True if this picking's company is Petrogulf Marine or a direct branch."""
        self.ensure_one()
        company = self.company_id
        if company.business_unit == 'pg_marine':
            return True
        return bool(company.parent_id and company.parent_id.business_unit == 'pg_marine')

    def _get_partner_company(self):
        """The res.company whose partner_id matches this picking's customer,
        if any - used to detect an internal manufacturer -> Marine handoff
        (company is the Fujairah manufacturer, customer is Marine itself)."""
        self.ensure_one()
        if not self.partner_id:
            return self.env['res.company']
        return self.env['res.company'].sudo().search([
            ('partner_id', '=', self.partner_id.commercial_partner_id.id),
        ], limit=1)

    def _is_pg_marine_partner(self):
        """True if this picking's customer is Petrogulf Marine itself."""
        self.ensure_one()
        return self._get_partner_company().business_unit == 'pg_marine'

    def _is_delivery_note_scope(self):
        """The shared Delivery Note report renders an Ajman, Power X or
        Marine layout (toggled internally by business_unit) - allow any of
        these scopes, plus deliveries from any company sold to Marine
        itself (manufacturer -> Marine handoff)."""
        self.ensure_one()
        return bool(self.sale_id) and (
            self._is_pg_ajman_company() or self._is_pg_powerx_company()
            or self._is_pg_marine_company() or self._is_pg_marine_partner()
        )