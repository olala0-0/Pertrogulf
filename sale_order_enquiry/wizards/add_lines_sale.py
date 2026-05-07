from odoo import api, models, fields, _, Command


class SalesLineAddWizard(models.TransientModel):
    _name = 'sale.line.wizard'

    type = fields.Selection([
        ('sale', 'Based On Sales'),
        ('customer', 'Based On Customer'),
        ('order_enq', 'Based On Order Inquiry'),
    ], string='Type', default='customer', required=True)

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    multi_order = fields.Boolean(string='Multiple Order')
    clear_add = fields.Boolean(string='Clear & Add Lines')
    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Sale Order',
        relation='sale_order_ids_rel',
        column1='wizard_id',
        column2='order_id'
    )

    sale_domain_ids = fields.Many2many(
        'sale.order',
        string='Sale Domain',
        relation='sale_domain_ids_rel',
        column1='wizard_id',
        column2='domain_id'
    )

    @api.onchange('type')
    def _onchange_type(self):
        self.sale_order_id, self.sale_order_ids = None, None
        context = self.env.context
        active_id = context.get('active_id')
        customer_id = context.get('customer_id')
        domain = [('id', '!=', active_id)]

        if self.type == 'customer' and customer_id:
            domain.append(('partner_id', '=', customer_id))
        elif self.type == 'order_enq':
            domain.append(('order_enquirey_id', '!=', False))

        sale_order = self.env['sale.order'].search(domain)
        self.sale_domain_ids = sale_order

    def get_order_line(self, model_id, sale_order_line, order, active_model):
        for line in order.order_line:
            order_line = {
                'display_type': line.display_type,
                'name': line.name,
                'price_unit': line.price_unit,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_uom_qty,
                'tax_id': [(6, 0, line.tax_id.ids)],
            }
            if active_model == 'sale.order':
                order_line['order_id'] = model_id.id
                order_line['product_id'] = line.product_id.id
            elif active_model == 'order.enq':
                order_line['enq_id'] = model_id.id
                order_line['product_id'] = line.product_id.product_tmpl_id.id

            sale_order_line.append(order_line)
        return sale_order_line

    def button_create_order_line(self):
        sale_order_line = []
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        model_id = self.env[active_model].browse(active_id)
        if not self.multi_order and self.sale_order_id:
            order = self.sale_order_id
            sale_order_line = self.get_order_line(model_id, sale_order_line, order, active_model)
        else:
            for order in self.sale_order_ids:
                sale_order_line = self.get_order_line(model_id, sale_order_line, order, active_model)

        if active_model == 'order.enq':
            model_id.update({'order_line_ids': [(Command.clear())]}) if self.clear_add else None
            self.env['order.enq.lines'].create(sale_order_line)
        elif active_model == 'sale.order':
            model_id.update({'order_line': [(Command.clear())]}) if self.clear_add else None
            self.env['sale.order.line'].create(sale_order_line)


class ProductAddWizard(models.TransientModel):
    _name = 'product.add.wizard'

    order_type = fields.Selection([
        ('single_sale', 'Single Sale Order'),
        ('multi_sale', 'Multi Sale Orders'),
    ], default='single_sale', string='Order Type')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Sale Order',
        relation='sales_order_ids_rel',
        column1='wizards_id',
        column2='orders_id'
    )

    sale_domain_ids = fields.Many2many(
        'sale.order',
        string='Sale Domain',
        relation='sales_domain_ids_rel',
        column1='wizards_id',
        column2='domains_id'
    )
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id, string='Company',
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id', readonly=True)
    product_id = fields.Many2one('product.template', string='Product', domain=[('sale_ok', '=', True)])
    price_unit = fields.Float('Unit Price')
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit Of Measure')
    tax_id = fields.Many2many(comodel_name='account.tax', string="Taxes", domain=[('type_tax_use', '=', 'sale')])

    @api.onchange('order_type')
    def onchange_order_line(self):
        domain = [('state', 'in', ('draft', 'sent'))]
        self.sale_domain_ids = self.env['sale.order'].search(domain)

    def button_add_product(self):
        lines = self.get_product()
        if self.order_type == 'single_sale':
            lines['order_id'] = self.sale_order_id.id
            self.env['sale.order.line'].create(lines)
        else:
            for rec in self.sale_order_ids:
                lines['order_id'] = rec.id
                self.env['sale.order.line'].create(lines)

    def get_product(self):
        product_id = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])
        lines = {
            'product_id': product_id.id,
            'name': self.product_id.name,
            'product_uom_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'product_uom': self.product_uom.id,
            'tax_id': [(6, 0, self.tax_id.ids)],
            'display_type': False,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
        }

        return lines


