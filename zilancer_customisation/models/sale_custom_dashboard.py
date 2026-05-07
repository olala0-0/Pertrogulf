from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class SalesPersonDashboard(models.Model):
    _name = 'sales.person.dashboard'
    _description = 'Sales Person Performance Dashboard'
    _rec_name = 'user_id'  # Makes the user name appear as the record name
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='Sales Person', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    
    # Performance metrics
    lead_count = fields.Integer(string='Leads', compute='_compute_counts')
    opportunity_count = fields.Integer(string='Opportunities', compute='_compute_counts')
    inquiry_count = fields.Integer(string='Sales Inquiries', compute='_compute_counts')
    quotation_count = fields.Integer(string='Sales Quotations', compute='_compute_counts')
    order_count = fields.Integer(string='Sales Orders', compute='_compute_counts')
    delivered_count = fields.Integer(string='Delivered', compute='_compute_counts')
    
    # Additional useful metrics
    total_revenue = fields.Monetary(string='Total Revenue', compute='_compute_revenue', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id.id)
    quotation_to_order_rate = fields.Float(string='Conversion Rate (%)', compute='_compute_conversion_rate', store=True)
    
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    
    @api.depends('user_id')
    def _compute_name(self):
        for record in self:
            if record.user_id:
                record.name = f"{record.user_id.name}'s Dashboard"
            else:
                record.name = "New Dashboard"
    
    @api.depends('user_id', 'company_id', 'date_from', 'date_to')
    def _compute_counts(self):
        for record in self:
            # Use the company environment for all searches
            self_with_company = self.with_company(self.env.company)
            # print("----self_with_company--------------", self_with_company)
            # print("----CONTEXTTTTTTTTTT--------------", self._context)
            # print("----companyyyyy------------------", self.env.user.company_ids,  self.env.context.get('allowed_company_ids', []))
            domain_user = [('user_id', '=', record.user_id.id)]
            domain_company = [('company_id', 'in', self.env.context.get('allowed_company_ids', []))]
            
            # Apply date filters if provided
            domain_date = []
            if record.date_from and record.date_to:
                domain_date = [
                    ('create_date', '>=', record.date_from),
                    ('create_date', '<=', record.date_to)
                ]
            
            # Count leads (not opportunities)
            lead_domain = domain_user + domain_company + domain_date + [('type', '=', 'lead')]
            record.lead_count = self_with_company.env['crm.lead'].with_context(active_test=True).search_count(lead_domain)
            
            # Count opportunities
            opportunity_domain = domain_user + domain_company + domain_date + [('type', '=', 'opportunity')]
            record.opportunity_count = self_with_company.env['crm.lead'].with_context(active_test=True).search_count(opportunity_domain)
            
            # Count sales inquiries
            inquiry_domain = domain_user + domain_company + domain_date
            record.inquiry_count = self_with_company.env['order.enq'].with_context(active_test=True).search_count(inquiry_domain)
            
            # Count quotations (not confirmed orders)
            quotation_domain = domain_user + domain_company + domain_date + [('state', 'in', ['draft', 'sent', 'approved'])]
            record.quotation_count = self_with_company.env['sale.order'].with_context(active_test=True).search_count(quotation_domain)
            
            # Count confirmed orders
            order_domain = domain_user + domain_company + domain_date + [('state', 'in', ['sale', 'done'])]
            record.order_count = self_with_company.env['sale.order'].with_context(active_test=True).search_count(order_domain)
            
            # Count delivered products - use proper company filtering
            delivery_domain = [
                ('sale_id.user_id', '=', record.user_id.id),
                ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
                ('state', '=', 'done')
            ]
            if domain_date:
                delivery_domain += domain_date
            record.delivered_count = self_with_company.env['stock.picking'].with_context(active_test=True).search_count(delivery_domain)
    
    @api.depends('user_id', 'company_id', 'date_from', 'date_to')
    def _compute_revenue(self):
        for record in self:
            # Use the company environment for revenue calculation
            self_with_company = self.with_company(self.env.company)
            
            domain = [
                ('user_id', '=', record.user_id.id),
                ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
                ('state', 'in', ['sale', 'done'])
            ]
            
            if record.date_from and record.date_to:
                domain += [
                    ('date_order', '>=', record.date_from),
                    ('date_order', '<=', record.date_to)
                ]
                
            orders = self_with_company.env['sale.order'].with_context(active_test=True).search(domain)
            record.total_revenue = sum(orders.mapped('amount_total'))
    
    @api.depends('quotation_count', 'order_count')
    def _compute_conversion_rate(self):
        for record in self:
            if record.quotation_count:
                record.quotation_to_order_rate = (record.order_count / record.quotation_count) * 100
            else:
                record.quotation_to_order_rate = 0
    
    def action_view_leads(self):
        self.ensure_one()
        action = self.env.ref('crm.crm_lead_all_leads').read()[0]
        domain = [
            ('user_id', '=', self.user_id.id),
            ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
            ('type', '=', 'lead')
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id
        }
        return action
    
    def action_view_opportunities(self):
        self.ensure_one()
        action = self.env.ref('crm.crm_lead_opportunities').read()[0]
        domain = [
            ('user_id', '=', self.user_id.id),
            ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
            ('type', '=', 'opportunity')
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id
        }
        return action
    
    def action_view_inquiries(self):
        self.ensure_one()
        action = self.env.ref('sale_order_enquiry.action_order_enquirey').read()[0]  # Adjust this to your module's action reference
        domain = [
            ('user_id', '=', self.user_id.id),
            ('company_id', 'in', self.env.context.get('allowed_company_ids', []))
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id
        }
        return action
    
    def action_view_quotations(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations').read()[0]
        domain = [
            ('user_id', '=', self.user_id.id),
            ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
            ('state', 'in', ['draft', 'sent'])
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id
        }
        return action

    def action_view_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        domain = [
            ('user_id', '=', self.user_id.id),
            ('company_id', 'in', self.env.context.get('allowed_company_ids', [])),
            ('state', 'in', ['sale', 'done'])
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id
        }
        return action

    def action_view_deliveries(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        domain = [
            ('sale_id.user_id', '=', self.user_id.id),
            ('sale_id.company_id', 'in', self.env.context.get('allowed_company_ids', [])),
            ('state', '=', 'done')
        ]
        if self.date_from and self.date_to:
            domain += [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to)
            ]
        action['domain'] = domain
        action['context'] = {
            'default_company_id': self.env.company.id
        }
        return action

    # @api.model
    # def default_get(self, fields):
    #     res = super(SalesPersonDashboard, self).default_get(fields)
    #     if not res.get('user_id') and 'user_id' in fields:
    #         res['user_id'] = self.env.user.id
    #     if not res.get('company_id') and 'company_id' in fields:
    #         res['company_id'] = self.env.company.id
    #     if not res.get('date_from') and 'date_from' in fields:
    #         res['date_from'] = fields.Date.today() - timedelta(days=30)
    #     if not res.get('date_to') and 'date_to' in fields:
    #         res['date_to'] = fields.Date.today()
    #     return res

    @api.model
    def _create_dashboard_for_sales_users(self):
        Dashboard = self.env['sales.person.dashboard']
        current_company = self.env.company
        # Get sales users for current company only
        sales_users = self.env['res.users'].search([
            # ('share', '=', False),
            # ('company_ids', 'in', current_company.id),
            # '|',
            # ('group_ids', 'in', self.env.ref('sales_team.group_sale_salesman').id),
            # ('group_ids', 'in', self.env.ref('sales_team.group_sale_manager').id),
        ])
        # Process each user
        for user in sales_users:
            # Find ALL dashboard records for this user (regardless of company)
            dashboards = Dashboard.search([
                ('user_id', '=', user.id)
            ], order='create_date ASC')
            if dashboards:
                # Keep only the oldest record, delete all others
                dashboards[1:].unlink()
            else:
                # No dashboard found, create one with current company
                Dashboard.create({
                    'user_id': user.id,
                    'company_id': current_company.id,
                    # 'date_from': fields.Date.today() - timedelta(days=30),
                    # 'date_to': fields.Date.today(),
                })
        return True

    @api.model
    def _update_all_dashboards(self):
        """
        Force recomputation of all dashboard data
        This can be called via a scheduled action (cron job)
        """
        dashboards = self.search([])
        dashboards._compute_counts()
        # dashboards._compute_revenue()
        # dashboards._compute_conversion_rate()
        return True


class SalesPerformance(models.Model):
    _name = 'sales.performance'
    _description = 'Sales Performance by Sales Person'

    salesperson = fields.Char(string='Sales Person')
    sales_metric = fields.Selection([
        ('leads', 'Leads'),
        ('opportunities', 'Opportunities'),
        ('sales_inquiries', 'Sales Inquiries'),
        ('sales_quotations', 'Sales Quotations'),
        ('sales_orders', 'Sales Orders'),
        ('delivered', 'Delivered')
    ], string='Sales Metric')
    value = fields.Integer(string='Value')

    def _create_sales_performance_data(self, salesperson_name, data):
        """
        Create sales performance data for a salesperson.
        Only creates records for metrics with values > 0.
        :param salesperson_name: Name of the salesperson
        :param data: Dictionary of sales metrics and their values
        """
        for metric, value in data.items():
            # Only create records for metrics with values > 0
            if value > 0:
                self.create({
                    'salesperson': salesperson_name,
                    'sales_metric': metric,
                    'value': value
                })
    
    @api.model
    def init(self):
        """
        Initialize the data with dynamic counts from CRM and Sales.
        This method is called when the module is installed/updated.
        Only include users who have at least one metric with value > 0.
        """
        # Clear existing records
        self.search([]).unlink()
        
        # Get all salespeople from res.users who are in sales groups
        salespeople = self.env['res.users'].search([
            ('group_ids', 'in', self.env.ref('sales_team.group_sale_salesman').id)
        ])
        
        for user in salespeople:
            # Get dynamic counts for the current user
            data = {
                'leads': self._get_lead_count(user.id),
                'opportunities': self._get_opportunity_count(user.id),
                'sales_inquiries': self._get_inquiry_count(user.id),
                'sales_quotations': self._get_quotation_count(user.id),
                'sales_orders': self._get_sales_order_count(user.id),
                'delivered': self._get_delivered_count(user.id)
            }
            
            # Only create data for users who have at least one non-zero value
            if any(value > 0 for value in data.values()):
                # Create data for the current user
                self._create_sales_performance_data(user.name, data)
    
    def _get_lead_count(self, user_id):
        """Get count of leads for a user"""
        return self.env['crm.lead'].search_count([
            ('user_id', '=', user_id),
            ('type', '=', 'lead')
        ])
    
    def _get_opportunity_count(self, user_id):
        """Get count of opportunities for a user"""
        return self.env['crm.lead'].search_count([
            ('user_id', '=', user_id),
            ('type', '=', 'opportunity')
        ])
    
    def _get_inquiry_count(self, user_id):
        """Get count of sales inquiries for a user"""
        # Assuming sales inquiries are leads/opportunities in a specific stage
        inquiry_stages = self.env['order.enq'].search([
            ('user_id', '=', user_id),
        ])
        
        return self.env['crm.lead'].search_count([
            ('user_id', '=', user_id),
            ('stage_id', 'in', inquiry_stages.ids)
        ])
    
    def _get_quotation_count(self, user_id):
        """Get count of quotations for a user"""
        return self.env['sale.order'].search_count([
            ('user_id', '=', user_id),
            ('state', 'in', ['draft', 'sent'])
        ])
    
    def _get_sales_order_count(self, user_id):
        """Get count of confirmed sales orders for a user"""
        return self.env['sale.order'].search_count([
            ('user_id', '=', user_id),
            ('state', '=', 'sale')
        ])
    
    def _get_delivered_count(self, user_id):
        """Get count of delivered sales orders for a user"""
        # Orders with completed deliveries
        delivered_orders_count = self.env['sale.order'].search_count([
            ('user_id', '=', user_id),
            ('picking_ids.state', '=', 'done')
        ])
        
        # Alternatively, count orders that are fully invoiced
        invoiced_orders_count = self.env['sale.order'].search_count([
            ('user_id', '=', user_id),
            ('invoice_status', '=', 'invoiced')
        ])
        
        # Use the greater count as some orders might be delivered but not invoiced or vice versa
        return max(delivered_orders_count, invoiced_orders_count)