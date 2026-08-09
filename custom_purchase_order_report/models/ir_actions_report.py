from odoo import models, _
from odoo.exceptions import UserError

AJMAN_SCOPED_REPORTS = {
    # 'custom_purchase_order_report.report_purchase_order_ajman': (
    #     'purchase.order',
    #     '_is_pg_ajman_scope',
    #     "This purchase order layout is only available for Petro Gulf Ajman and its branch companies.",
    # ),
    'custom_purchase_order_report.report_despatch_note_ajman': (
        'stock.picking',
        '_is_pg_ajman_scope',
        "This despatch note layout is only available for sale deliveries of "
        "Petro Gulf Ajman and its branch companies.",
    ),
    'custom_purchase_order_report.report_grn_ajman': (
        'stock.picking',
        '_is_pg_ajman_grn_scope',
        "This goods receipt note layout is only available for incoming receipts of "
        "Petro Gulf Ajman and its branch companies.",
    ),
}


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report_sudo = self._get_report(report_ref)
        scoped = AJMAN_SCOPED_REPORTS.get(report_sudo.report_name)
        if scoped and res_ids:
            model_name, check_method, error_message = scoped
            records = self.env[model_name].browse(res_ids)
            if any(not getattr(record, check_method)() for record in records):
                raise UserError(_(error_message))
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)