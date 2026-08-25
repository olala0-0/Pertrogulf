from odoo import models, fields, api
from odoo.addons.sale_order_enquiry.business_unit_data import BUSINESS_UNIT_SELECTION


class region_code(models.Model):
    _name = 'region.code'

    name = fields.Char("Region Code")
    country_region_id = fields.Many2one('res.country', string="Country")


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char(string="Name", required=True)


class ContractStatus(models.Model):
    _name = 'contract.status'
    _description = 'Contract Status'

    name = fields.Char(string="Name", required=True)


class PartnerContract(models.Model):
    _name = 'partner.contract'
    _description = 'Partner Contract'

    partner_id = fields.Many2one('res.partner', string="Contact")
    contract_type_id = fields.Many2one('contract.type', string="Contract Type", required=True)
    contract_status_id = fields.Many2one('contract.status', string="Contract Status", required=True)
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    alert_before = fields.Integer(string="Alert Before (days)")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        required=True,
    )
    sbu_name = fields.Char(string="SBU Name")
    whatsapp_number = fields.Char("Whatsapp Number")
    website = fields.Char("Website", default="www.")
    sort_name = fields.Char("Short Name")
    parent_sort_name = fields.Char(related="parent_id.sort_name", store=True)
    facebook = fields.Char("Facebook")
    instagram = fields.Char("Instagram")
    linkedin = fields.Char("LinkedIn")
    twitter = fields.Char("Twitter (X)")
    tiktok = fields.Char("TikTok")
    youtube = fields.Char("YouTube")
    pinterest = fields.Char("Pinterest")
    snapchat = fields.Char("Snapchat")
    whatsapp = fields.Char("WhatsApp")
    reddit = fields.Char("Reddit")
    wechat = fields.Char("WeChat")
    telegram = fields.Char("Telegram")
    twitch = fields.Char("Twitch")
    discord = fields.Char("Discord")
    tumblr = fields.Char("Tumblr")
    vimeo = fields.Char("Vimeo")
    sina_weibo = fields.Char("Sina Weibo")
    nextdoor = fields.Char("Nextdoor")
    quora = fields.Char("Quora")
    yelp = fields.Char("Yelp")
    display_name = fields.Char(compute="_compute_display_name")
    region_code_id = fields.Many2one('region.code', string="Region Code")
    contract_ids = fields.One2many('partner.contract', 'partner_id', string="Contracts")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    total_revenue = fields.Float(
        string="Total Revenue",
        compute='_compute_total_revenue',
    )

    quotation_count = fields.Integer(
        string="Quotation Count",
        groups='sales_team.group_sale_salesman',
        compute='_compute_quotation_count',
    )

    def _compute_sale_order_count(self):
        self.sale_order_count = 0
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            return

        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', self.ids)],
            ['parent_id'],
        )
        sale_order_groups = self.env['sale.order']._read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('state', '=', 'sale')],
            groupby=['partner_id'], aggregates=['__count']
        )
        self_ids = set(self._ids)

        for partner, count in sale_order_groups:
            while partner:
                if partner.id in self_ids:
                    partner.sale_order_count += count
                partner = partner.parent_id

    def _compute_quotation_count(self):
        self.quotation_count = 0
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            return

        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', self.ids)],
            ['parent_id'],
        )
        quotation_groups = self.env['sale.order']._read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('state', 'in', ['draft', 'sent'])],
            groupby=['partner_id'], aggregates=['__count']
        )
        self_ids = set(self._ids)

        for partner, count in quotation_groups:
            while partner:
                if partner.id in self_ids:
                    partner.quotation_count += count
                partner = partner.parent_id

    def action_view_sale_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        action['domain'] = [('partner_id', 'child_of', self.id), ('state', '=', 'sale')]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_quotations(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        action['name'] = self.env._('Quotations')
        action['domain'] = [('partner_id', 'child_of', self.id), ('state', 'in', ['draft', 'sent'])]
        action['context'] = {'default_partner_id': self.id}
        return action

    def _compute_total_revenue(self):
        for partner in self:
            print("---partner.total_revenue--------------------", partner.total_revenue)
            # Find all child contacts
            all_partners = self.env['res.partner'].search([('id', 'child_of', partner.id)])

            # Get confirmed sale orders linked to those partners
            sale_orders = self.env['sale.order'].search([
                ('partner_id', 'in', all_partners.ids),
                ('state', 'in', ['sale', 'done'])  # only confirmed orders
            ])

            # Sum the revenue
            partner.total_revenue = sum(sale_orders.mapped('amount_total'))
            print("--partner.total_revenue--------------", partner.total_revenue)

    def fetch_sort_name(self):
        for rec in self.search([]):
            rec.sort_name = rec.name

    @api.onchange('mobile')
    def _onchange_mobile_set_whatsapp(self):
        if self.mobile:
            self.whatsapp_number = self.mobile

    @api.onchange('name')
    def _onchange_name_sort(self):
        if self.name:
            self.sort_name = self.name

    # def name_get(self):
    #     result = []
    #     for partner in self:
    #         name = partner.name or ""
    #         if partner.company_type == 'person':
    #             # For individuals: Name, Sort Name
    #             if partner.sort_name:
    #                 display_name = f"{name}, {partner.sort_name}"
    #             else:
    #                 display_name = name
    #         else:
    #             # For companies or others: default name
    #             display_name = name
    #         result.append((partner.id, display_name))
    #     return result

    @api.depends('sort_name', 'company_type')
    def _compute_display_name(self):
        for partner in self:
            name = partner.name or ""
            if partner.company_type == 'person':
                # For individuals: Name, Sort Name
                if partner.parent_id and partner.parent_id.sort_name:
                    display_name = f"{name}, {partner.parent_id.sort_name}"
                else:
                    display_name = name
            elif partner.company_type == 'company':
                if partner.sort_name:
                    display_name = f"{partner.sort_name}"
                else:
                    display_name = name
            else:
                # For companies or others: default name
                display_name = name
            partner.display_name = display_name

    # @api.model
    # def create(self, vals):
    #     """Auto-populate website from parent company during creation"""
    #     if vals.get('parent_id') and not vals.get('website'):
    #         parent = self.browse(vals['parent_id'])
    #         if parent.website:
    #             vals['website'] = parent.website
    #     return super(ResPartner, self).create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate website from parent company during creation"""
        for vals in vals_list:
            if vals.get('parent_id') and not vals.get('website'):
                parent = self.browse(vals['parent_id'])
                if parent.website:
                    vals['website'] = parent.website
        return super(ResPartner, self).create(vals_list)
