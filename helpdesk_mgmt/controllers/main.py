import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):

    @http.route('/sales/performance', type='http', auth='user')
    def sales_performance(self, **kw):
        # Get filtered salesperson
        salesperson = kw.get('salesperson')
        
        # Get all salespeople for dropdown
        all_salespeople = request.env['sales.performance'].sudo().search([]).mapped('salesperson')
        all_salespeople = sorted(list(set(all_salespeople)))
        
        # Get sales performance data
        domain = [('salesperson', '=', salesperson)] if salesperson else []
        performance_data = request.env['sales.performance'].sudo().search(domain)
        
        # Process data for the graph
        data = {}
        salespeople = set()
        for record in performance_data:
            salespeople.add(record.salesperson)
            data[(record.salesperson, record.sales_metric)] = record.value
        
        # If filtering by salesperson but no data found, show empty data
        if salesperson and not salespeople:
            salespeople = {salesperson}
        
        # Sort salespeople for consistent ordering
        salespeople = sorted(list(salespeople))
        
        # Define metrics and their labels
        metrics = ['leads', 'opportunities', 'sales_inquiries', 'sales_quotations', 'sales_orders', 'delivered']
        labels = {
            'leads': 'Leads',
            'opportunities': 'Opportunities',
            'sales_inquiries': 'Sales Inquiries',
            'sales_quotations': 'Sales Quotations',
            'sales_orders': 'Sales Orders',
            'delivered': 'Delivered'
        }
        
        # Define colors for metrics
        colors = {
            'leads': '#1f77b4',
            'opportunities': '#ff7f0e',
            'sales_inquiries': '#2ca02c',
            'sales_quotations': '#17becf',
            'sales_orders': '#9467bd',
            'delivered': '#8c564b'
        }
        
        # Find maximum value for scaling
        max_value = 1  # Default to 1 to avoid division by zero
        for value in data.values():
            max_value = max(max_value, value)
        
        # Render template
        return request.render('sales_performance.sales_performance_report_page', {
            'salesperson': salesperson,
            'all_salespeople': all_salespeople,
            'salespeople': salespeople,
            'metrics': metrics,
            'labels': labels,
            'colors': colors,
            'data': data,
            'max_value': max_value
        })
        
    @http.route('/sales/performance/dharmesh', type='http', auth='user')
    def sales_performance_dharmesh(self, **kw):
        # Specific endpoint to show only Dharmesh's data
        return self.sales_performance(salesperson='Dharmesh')

    @http.route("/ticket/close", type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        ticket = (
            http.request.env["helpdesk.ticket"]
            .sudo()
            .search([("id", "=", values["ticket_id"])])
        )
        stage = http.request.env["helpdesk.ticket.stage"].browse(values.get("stage_id"))
        if stage.close_from_portal:  # protect against invalid target stage request
            ticket.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect("/my/ticket/" + str(ticket.id))

    def _get_teams(self):
        return (
            http.request.env["helpdesk.ticket.team"]
            .with_company(request.env.company.id)
            .search([("active", "=", True), ("show_in_portal", "=", True)])
            if http.request.env.user.company_id.helpdesk_mgmt_portal_select_team
            else False
        )

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        session_info = http.request.env["ir.http"].session_info()
        company = request.env.company
        category_model = http.request.env["helpdesk.ticket.category"]
        categories = category_model.with_company(company.id).search(
            [("active", "=", True)]
        )
        email = http.request.env.user.email
        name = http.request.env.user.name
        company = request.env.company
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {
                "categories": categories,
                "teams": self._get_teams(),
                "email": email,
                "name": name,
                "ticket_team_id_required": (
                    company.helpdesk_mgmt_portal_team_id_required
                ),
                "ticket_category_id_required": (
                    company.helpdesk_mgmt_portal_category_id_required
                ),
                "max_upload_size": session_info["max_file_upload_size"],
            },
        )

    def _prepare_submit_ticket_vals(self, **kw):
        category = http.request.env["helpdesk.ticket.category"].browse(
            int(kw.get("category"))
        )
        company = category.company_id or http.request.env.company
        vals = {
            "company_id": company.id,
            "category_id": category.id,
            "description": plaintext2html(kw.get("description")),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env.ref(
                "helpdesk_mgmt.helpdesk_ticket_channel_web", False
            ).id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
        }
        team = http.request.env["helpdesk.ticket.team"]
        if company.helpdesk_mgmt_portal_select_team and kw.get("team"):
            team = (
                http.request.env["helpdesk.ticket.team"]
                .sudo()
                .search(
                    [("id", "=", int(kw.get("team"))), ("show_in_portal", "=", True)]
                )
            )
            vals["team_id"] = team.id
        # Need to set stage_id so that the _track_template() method is called
        # and the mail is sent automatically if applicable
        vals["stage_id"] = team._get_applicable_stages()[:1].id
        return vals

    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        vals = self._prepare_submit_ticket_vals(**kw)
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        return werkzeug.utils.redirect(f"/my/ticket/{new_ticket.id}")
