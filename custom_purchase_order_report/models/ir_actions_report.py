from odoo import models, _
from odoo.exceptions import UserError

AJMAN_PO_REPORT = 'custom_purchase_order_report.report_purchase_order_ajman'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report_sudo = self._get_report(report_ref)
        if report_sudo.report_name == AJMAN_PO_REPORT and res_ids:
            orders = self.env['purchase.order'].browse(res_ids)
            if any(not order._is_pg_ajman_scope() for order in orders):
                raise UserError(_(
                    "This purchase order layout is only available for Petro Gulf "
                    "Ajman and its branch companies."
                ))
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)