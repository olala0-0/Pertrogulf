from odoo import models, _
from odoo.exceptions import UserError

AJMAN_SCOPED_REPORTS = {
    'custom_sale_quotation_report.report_proforma_invoice_ajman': (
        'sale.order',
        '_is_proforma_invoice_scope',
        "This proforma invoice layout is only available for sale orders of "
        "Petro Gulf Ajman, Power X and their branch companies.",
    ),
    'custom_sale_quotation_report.report_tax_invoice_ajman': (
        'account.move',
        '_is_tax_invoice_scope',
        "This tax invoice layout is only available for invoices of "
        "Petro Gulf Ajman, Power X, Petrogulf Marine and their branch companies.",
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