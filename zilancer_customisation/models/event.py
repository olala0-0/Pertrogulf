from odoo import models, fields, api
from odoo.tools import format_amount
from odoo.addons.sale_order_enquiry.business_unit_data import BUSINESS_UNIT_SELECTION


class EventSummary(models.Model):
    _name = 'event.summary'
    _description = 'Event Summary Line'

    category = fields.Selection([
        ('dos', "Do's"),
        ('donts', "Don'ts"),
        ('learnings', "Learnings"),
        ('remarks', "Remarks"),
        ('competitor', 'Competitor'),
    ], string="Category", required=True)

    remarks = fields.Text(string="Remarks")
    event_id = fields.Many2one('event.event', string="Event", ondelete='cascade')


class EventResponsible(models.Model):
    _name = 'responsible.team'
    _description = 'Responsible Team'

    name = fields.Char('Name', required=True)


class Event(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'image.mixin']

    responsible_team = fields.Selection([
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('hr', 'HR'),
        ('it', 'IT'),
        ('finance', 'Finance'),
    ], string="Responsible Team")

    responsible_team_id = fields.Many2one('responsible.team', string="Responsible Team")

    line_of_business = fields.Char(string="Line of Business")
    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        required=True,
    )

    relevance_category = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string="Relevance Category", default='medium')

    comp_name = fields.Char(string="Company Name")
    contact_name = fields.Char(string="Contact Name")
    designation = fields.Char(string="Designation")
    email = fields.Char(string="Email")
    phone_no = fields.Char(string="Phone No")
    website = fields.Char(string="Website")

    category = fields.Selection([
        ('visitor', 'Visitor'),
        ('customer', 'Customer'),
        ('competitor', 'Competitor'),
        ('sponsor', 'Sponsor'),
    ], string="Category")

    subcategory = fields.Selection([
        ('visitor_general', 'Visitor - General'),
        ('visitor_interested', 'Visitor - Interested'),
        ('visitor_highly_interested', 'Visitor - Highly Interested'),
        ('visitor_enquired', 'Visitor - Enquired'),
        ('customer_general', 'Customer - General'),
        ('customer_interested', 'Customer - Interested'),
        ('customer_highly_interested', 'Customer - Highly Interested'),
        ('customer_enquired', 'Customer - Enquired'),
        ('competitor_lubricant', 'Competitor - Lubricant'),
        ('sponsor_title', 'Sponsor - Title Sponsor'),
        ('sponsor_bronze', 'Sponsor - Bronze'),
        ('sponsor_silver', 'Sponsor - Silver'),
        ('sponsor_gold', 'Sponsor - Gold'),
        ('sponsor_platinum', 'Sponsor - Platinum'),
    ], string="Subcategory")
    event_summary_ids = fields.One2many(
        'event.summary', 'event_id', string="Event Summaries"
    )
    avaliable_event_ticket_ids = fields.One2many('event.event.ticket', 'event_avalible_id', string='Available Options', copy=True, readonly=False)
    venue = fields.Char(string="Venue")
    opportunity_volume = fields.Char("Opportunity Volume")
    opportunity_revenue = fields.Char("Opportunity Revenue")
    remarks = fields.Char("Remarks")
    # total_amount = fields.Float(compute="_compute_total_amount", "Total Amount")
    # def _compute_total_amount(self):
    #     for rec in self:
    #         rec.total_amount = sum(rec.event_ticket_ids.mapped('price')) or 0.0
    total_amount = fields.Float(compute="_compute_total_amount", string="Amounts")
    formatted_total_amount = fields.Char(compute="_compute_total_amount", string="Total Amount")
    # image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    avatar_128 = fields.Image("Avatar", related='image_1920', max_width=128, max_height=128, store=True)
    port_master_id = fields.Many2one('region.code', string='Region Code')
    country_region_id = fields.Many2one('res.country', string="Country")

    registration_count = fields.Integer(
        string="Number of Attendees",
        compute="_compute_registration_count",
        store=True
    )

    @api.depends('registration_ids')
    def _compute_registration_count(self):
        for event in self:
            event.registration_count = len(event.registration_ids)

    @api.onchange('port_master_id')
    def onchange_port_master_id(self):
        if self.port_master_id:
            self.country_region_id = self.port_master_id.country_region_id.id

    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.event_ticket_ids.mapped('price')) or 0.0
            rec.formatted_total_amount = "$%.2f" % rec.total_amount

    # Opportunity Volume  - Plain Text USD 12,000
    # Opportunity Revenue - Plain Text 
    # Remarks         - Plain Text 
    # Total Amount        - disabled field with $ prefix


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    comp_name = fields.Char(string="Company Name")
    contact_name = fields.Char(string="Contact Name")
    designation = fields.Char(string="Designation")
    email = fields.Char(string="Email")
    phone_no = fields.Char(string="Phone No")
    website = fields.Char(string="Website")

    category = fields.Selection([
        ('visitor', 'Visitor'),
        ('customer', 'Customer'),
        ('competitor', 'Competitor'),
        ('sponsor', 'Sponsor'),
    ], string="Category")

    subcategory = fields.Selection([
        ('visitor_general', 'Visitor - General'),
        ('visitor_interested', 'Visitor - Interested'),
        ('visitor_highly_interested', 'Visitor - Highly Interested'),
        ('visitor_enquired', 'Visitor - Enquired'),
        ('customer_general', 'Customer - General'),
        ('customer_interested', 'Customer - Interested'),
        ('customer_highly_interested', 'Customer - Highly Interested'),
        ('customer_enquired', 'Customer - Enquired'),
        ('competitor_lubricant', 'Competitor - Lubricant'),
        ('sponsor_title', 'Sponsor - Title Sponsor'),
        ('sponsor_bronze', 'Sponsor - Bronze'),
        ('sponsor_silver', 'Sponsor - Silver'),
        ('sponsor_gold', 'Sponsor - Gold'),
        ('sponsor_platinum', 'Sponsor - Platinum'),
    ], string="Subcategory")
    hq_location = fields.Char(string="HQ Location")
    industry_segment = fields.Char(string="Industry Segment")
    vessel_fleet_size = fields.Char(string="Vessel Fleet Size")
    major_lubricant_grade_1 = fields.Char(string="Major Lubricant Grade 1")
    qty_1 = fields.Float(string="Qty 1")
    major_lubricant_grade_2 = fields.Char(string="Major Lubricant Grade 2")
    qty_2 = fields.Float(string="Qty 2")
    major_lubricant_grade_3 = fields.Char(string="Major Lubricant Grade 3")
    qty_3 = fields.Float(string="Qty 3")
    annual_consumption = fields.Char(string="Annual Consumption")
    remarks = fields.Text(string="Remarks")


class EventTickets(models.Model):
    _inherit = 'event.event.ticket'

    currency = fields.Char("Currency", default="$")
    event_avalible_id = fields.Many2one('event.event', string="Event")

    def _get_ticket_multiline_description(self):
        return '%s\n%s' % (self.product_id.name, self.product_id.name)

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
