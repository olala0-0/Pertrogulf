from odoo import models, fields, api


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

    business_unit = fields.Selection([
        ('pg_marine', 'PG-Marine'),
        ('pg_auto', 'PG-Auto'),
        ('pg_powerx', 'PG-PowerX'),
        ('pg_aviation', 'PG-Aviation'),
        ('pg_tblnd', 'PG-Toll Blending')
    ], string="Business Unit", required=True)
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

    @api.model
    def create(self, vals):
        """Auto-populate website from parent company during creation"""
        if vals.get('parent_id') and not vals.get('website'):
            parent = self.browse(vals['parent_id'])
            if parent.website:
                vals['website'] = parent.website
        return super(ResPartner, self).create(vals)
