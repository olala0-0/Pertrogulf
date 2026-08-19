from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.sale_order_enquiry.business_unit_data import (
    BUSINESS_UNIT_SELECTION,
    get_business_unit_prefix,
)
from datetime import datetime


class OrderEnquiry(models.Model):
    _name = "order.enq"
    _order = "sequence, date_order, id"

    name = fields.Char(
        string="Inquiry Number",
        default=lambda self: _("New"),
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, string="Company"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    user_id = fields.Many2one(
        "res.users", string="Inquiry BY", default=lambda self: self.env.user
    )
    # partner_id = fields.Many2one('res.partner', string='Customer',  required=True, domain=[('type', '!=', 'private')])
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain=lambda self: [
            ("type", "!=", "private"),
            ("company_id", "in", [self.env.company.id, False]),
        ],
    )
    email = fields.Char(string="Email")
    # state = fields.Selection([('pending', 'Pending'), ('confirm', 'Confirmed'), ('cancel', 'cancel')], default='pending', string='state')
    state = fields.Selection(
        [
            ("inquiry", "Inquiry"),
            ("convert_quote", "Converted to Quote"),
            ("convert_order", "Converted to Order"),
            ("cancel", "cancel"),
        ],
        default="inquiry",
        string="state",
    )
    order_line_ids = fields.One2many(
        "order.enq.lines", "enq_id", string="Order Line", copy=True
    )
    sale_order_id = fields.Many2one("sale.order", string="Sale Order")
    sale_order_ids = fields.Many2many("sale.order", string="Sale Order's")
    multi_order = fields.Boolean("Multi Orders")
    sale_count = fields.Integer(compute="compute_sale_count", store=True)
    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
    )
    color = fields.Integer(string="Color Index")
    note = fields.Text("Note")
    date_order = fields.Datetime(
        string="Inquiry Date",
        required=True,
        readonly=False,
        copy=False,
        help="Inquiry Date",
        default=fields.Datetime.now,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    vessel_no = fields.Char(string="Vessel")
    imo_number = fields.Char(string="IMO")

    vessel_no_id = fields.Many2one("vessel.no", string="Vessel Name")
    imo_no_id = fields.Many2one("imo.number", string="IMO Number")

    delivery_by_barge = fields.Boolean(string="Delivery by Barge")
    delivery_by_id = fields.Many2one("delivery.by", string="Delivery By")
    # port_name = fields.Char(string="Port Name")
    country_port_id = fields.Many2one("res.country", string="Country of Supply")
    # outside_anchorside = fields.Selection([
    #     ('outside', 'Outside'),
    #     ('anchorside', 'Anchorside')
    # ], string="Outside / Anchorside")
    outside_anchorside = fields.Selection(
        [
            ("alongside", "Alongside"),
            ("anchorage", "Anchorage"),
            ("delivered_to_agent", "Delivered to Agent"),
            ("delivered_to_warehouse", "Delivered to Warehouse"),
        ],
        string="Delivery Type",
    )
    delivery_type_id = fields.Many2one("delivery.type", string="Delivery Type")
    sales_order_received = fields.Boolean(string="Sales Order Received")
    sales_order_date = fields.Date(string="Sales Order Date")
    po_received = fields.Boolean(string="PO Received")
    po_number = fields.Char(string="PO Number")
    purchase_order_date = fields.Date(string="Purchase Order Date")
    production_started = fields.Boolean(string="Production Started")
    expected_closure_date = fields.Char(string="Expected Closure Date")
    production_date = fields.Date(string="Production Date")
    expected_date_of_completion = fields.Date(string="Expected Date of Completion")
    # amount_untaxed = fields.Monetary(string="Untaxed Amount", store=True, compute='_compute_amounts', tracking=5)
    # amount_tax = fields.Monetary(string="Taxes", store=True, compute='_compute_amounts')
    # amount_total = fields.Monetary(string="Total", store=True, compute='_compute_amounts', tracking=4)
    # tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        default=lambda self: self.env.company.business_unit
    )
    # default=lambda self: self.env.company.business_unit
    # master_brand = fields.Char(string="Master Brand")
    brand_type = fields.Char(string="Brand Type")
    country_id = fields.Many2one("res.country", string="Country")
    inquiry_rec_from = fields.Char(string="Inquiry Received From")
    brand_master_id = fields.Many2one("brand.master", string="Master Brand")
    port_master_id = fields.Many2one("port.master", string="Port Name")
    port_note = fields.Html("Notes")
    vessel_eta = fields.Datetime(string="Vessel ETA")
    vessel_eta_message = fields.Char(
        compute="_compute_vessel_eta_message", string="Vessel Arriving In"
    )
    operational_status = fields.Selection(
        [("present", "Present"), ("not_present", "Not Present")],
        string="Operational Status @ Port",
        default="present",
    )
    sales_user_id = fields.Many2one("res.users", string="Sales Person")
    total_quantity = fields.Float(
        compute="_compute_total_quantity", string="Total Quantity"
    )
    total_qty_units = fields.Float(
        compute="_compute_total_qty_units", string="Total Qty in L"
    )
    reason_id = fields.Many2one("sale.reason", string="Reason for losing inquiry")
    pricing = fields.Char("Pricing")
    port_issue = fields.Char("Port Issue")
    timeline_shortage = fields.Char("Timeline Shortage")
    out_of_service_area = fields.Char("Out of Service Area")
    process_stage_id = fields.Many2one("process.stage", string="Process Stage")
    new_existing = fields.Selection(
        [
            ("new", "New"),
            ("existing", "Existing"),
        ],
        string="Inquiry Type",
    )
    Source_of_inquiry_id = fields.Many2one("source.inquiry", string="Source of Inquiry")
    mode_payments = fields.Char("Mode/Terms of Payment")
    post_tally_date = fields.Datetime(string="Posted to Tally Date Time")
    customer_user_id = fields.Many2one(
        related="partner_id.user_id", string="Customer Sales Person", store=True
    )
    active = fields.Boolean("Active", default=True)
    toll_sale_type = fields.Selection(
        [("rm", "Raw Material"), ("fg", "Finished Goods")], string="Sale Type"
    )
    # RM – Raw Material
    # FG – Finished Goods

    def _compute_total_qty_units(self):
        for rec in self:
            rec.total_qty_units = sum(rec.order_line_ids.mapped("unit_qty")) or 0

    # @api.depends('vessel_eta')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_quantity = sum(rec.order_line_ids.mapped("product_uom_qty")) or 0

    @api.onchange("vessel_no_id")
    def _onchange_vessel_no_id(self):
        if self.vessel_no_id and self.vessel_no_id.imo_number:
            self.imo_number = self.vessel_no_id.imo_number

    def write(self, vals):
        res = super().write(vals)
        for order in self:
            if (
                order.sales_user_id
                and order.partner_id
                and not order.partner_id.user_id
            ):
                order.partner_id.user_id = order.sales_user_id
        return res

    @api.onchange("partner_id")
    def _onchange_partner_id_check_existing_orders(self):
        for rec in self:
            if rec.partner_id:
                rec.sales_user_id = rec.partner_id.user_id
                rec.email = rec.partner_id.email
                # rec.payment_term_id = rec.partner_id.email
                # Check for confirmed sale orders with at least one delivery
                sale_orders = self.env["sale.order"].search(
                    [
                        ("partner_id", "=", rec.partner_id.id),
                        ("state", "=", "sale"),
                        ("picking_ids", "!=", False),
                    ],
                    limit=1,
                )
                if sale_orders:
                    rec.new_existing = "existing"
                else:
                    rec.new_existing = "new"

    @api.depends("vessel_eta")
    def _compute_vessel_eta_message(self):
        for order in self:
            if order.vessel_eta:
                delta = order.vessel_eta - fields.Datetime.now()
                days = delta.days
                hours = delta.seconds // 3600
                if days > 1:
                    order.vessel_eta_message = f"Vessel arriving in {days} days"
                elif days == 1:
                    order.vessel_eta_message = f"Vessel arriving in 1 day"
                else:
                    order.vessel_eta_message = f"Vessel arriving in {hours} hours"
            else:
                order.vessel_eta_message = "No ETA set"

    # @api.onchange('vessel_eta')
    # def _onchange_vessel_eta(self):
    #     if self.vessel_eta:
    #         now = fields.Datetime.now()
    #         eta = self.vessel_eta
    #         difference = eta - now

    #         if difference.total_seconds() <= 0:
    #             message = _("The vessel has already arrived.")
    #         else:
    #             hours = difference.total_seconds() / 3600
    #             if hours < 24:
    #                 message = _("Vessel arriving in %d hours") % int(hours)
    #             else:
    #                 days = hours / 24
    #                 message = _("Vessel arriving in %d days") % int(days)

    #         # Raise a UserError to display the message
    #         raise UserError(message)

    @api.onchange("port_master_id")
    def onchange_port_master_id(self):
        if self.port_master_id:
            self.country_id = self.port_master_id.country_id.id
            self.port_note = self.port_master_id.note

    @api.onchange("brand_master_id")
    def onchange_brand_master_id(self):
        if self.brand_master_id:
            self.brand_type = self.brand_master_id.brand_type

    @api.depends("sale_order_ids")
    def compute_sale_count(self):
        if self.sale_order_id:
            self.sale_count = len(self.sale_order_ids)
        else:
            self.sale_count = None

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Get the current month abbreviation and year
            if vals.get("name", _("New")) == _("New"):
                bu = vals.get("business_unit")
                if not bu:
                    raise UserError("Business Unit is required to generate the sequence.")

                prefix = get_business_unit_prefix(bu) or "PG"

                # Month & Year
                now = datetime.now()
                month = now.strftime("%b").upper()  # APR
                year = now.strftime("%Y")  # 2025

                # Build full prefix
                full_prefix = f"{prefix}-INQ-{month}-{year}-"

                # Find existing inquiries with same prefix to count
                last = self.search(
                    [("name", "ilike", full_prefix)], order="id desc", limit=1
                )
                if last and last.name:
                    try:
                        last_number = int(last.name.split("-")[-1])
                        number = last_number + 1
                    except ValueError:
                        number = 1
                else:
                    number = 1

                vals["name"] = f"{full_prefix}{str(number).zfill(7)}"
        res = super(OrderEnquiry, self).create(vals_list)
        for record in res:
            if record.sales_user_id and record.partner_id and not record.partner_id.user_id:
                record.partner_id.user_id = record.sales_user_id
        return res

    def button_cancel(self):
        if self.state == "inquiry":
            self.state = "cancel"

    def button_multi_orders(self):
        sales_list = [self.sale_order_id.id]
        self.button_confirm(sales_list)

    # def button_confirm(self, sales_list=None):
    #     if len(self.order_line_ids) <= 0:
    #         raise ValidationError(_("Before Confirm Please Add Product"))

    #     # Generate inquiry sequence based on business unit
    #     def generate_inquiry_sequence(business_unit):
    #         if not business_unit:
    #             # Use default sequence if no business unit
    #             return self.env['ir.sequence'].next_by_code('order.enquiry') or 'INQ/NEW'

    #         # Mapping to prefix format
    #         bu_prefix = {
    #             'pg_marine': 'PG-MARINE',
    #             'pg_auto': 'PG-AUTO',
    #             'pg_powerx': 'PG-POWERX',
    #             'pg_aviation': 'PG-AVIATION',
    #         }.get(business_unit)

    #         if not bu_prefix:
    #             # Fallback to default if invalid business unit
    #             return self.env['ir.sequence'].next_by_code('order.enquiry') or 'INQ/NEW'

    #         try:
    #             from datetime import datetime
    #             now = datetime.now()
    #             month = now.strftime('%b').upper()  # MAY
    #             year = now.strftime('%Y')           # 2025
    #             sequence_code = f'{bu_prefix}-INQ-{month}-{year}'

    #             # Check if sequence exists, create if not
    #             seq = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)
    #             if not seq:
    #                 seq = self.env['ir.sequence'].sudo().create({
    #                     'name': f'{bu_prefix} Inquiry {month} {year}',
    #                     'code': sequence_code,
    #                     'prefix': f'{bu_prefix}-INQ-{month}-{year}-',
    #                     'padding': 7,  # For 7-digit padding (0000001)
    #                     'number_next': 1,
    #                     'number_increment': 1,
    #                 })

    #             # Generate next number
    #             next_name = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
    #             return next_name or self.env['ir.sequence'].next_by_code('order.enquiry') or 'INQ/NEW'

    #         except Exception as e:
    #             print(f"Error generating inquiry sequence: {e}")
    #             # Fallback to default sequence
    #             return self.env['ir.sequence'].next_by_code('order.enquiry') or 'INQ/NEW'

    #     # Generate and set the inquiry sequence
    #     business_unit = getattr(self, 'business_unit', None)
    #     inquiry_sequence = generate_inquiry_sequence(business_unit)

    #     # Update the current inquiry record with the generated sequence
    #     self.name = inquiry_sequence  # Assuming 'name' field stores the sequence
    #     print(f"Generated inquiry sequence: {inquiry_sequence}")

    #     # Generate the sale order name
    #     def generate_sale_order_name(business_unit):
    #         if not business_unit:
    #             return self.env['ir.sequence'].next_by_code('sale.order') or 'SO/NEW'

    #         bu_prefix = {
    #             'pg_marine': 'PG-MARINE',
    #             'pg_auto': 'PG-AUTO',
    #             'pg_powerx': 'PG-POWERX',
    #             'pg_aviation': 'PG-AVIATION',
    #         }.get(business_unit)

    #         if not bu_prefix:
    #             return self.env['ir.sequence'].next_by_code('sale.order') or 'SO/NEW'

    #         try:
    #             from datetime import datetime
    #             now = datetime.now()
    #             month = now.strftime('%b').upper()
    #             year = now.strftime('%Y')
    #             sequence_code = f'{bu_prefix}-SQ-{month}-{year}'

    #             seq = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)
    #             if not seq:
    #                 seq = self.env['ir.sequence'].sudo().create({
    #                     'name': f'{bu_prefix} Sales Quotation {month} {year}',
    #                     'code': sequence_code,
    #                     'prefix': f'{bu_prefix}-SQ-{month}-{year}-',
    #                     'padding': 4,
    #                     'number_next': 1,
    #                     'number_increment': 1,
    #                 })

    #             next_name = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
    #             return next_name or self.env['ir.sequence'].next_by_code('sale.order') or 'SO/NEW'

    #         except Exception as e:
    #             print(f"Error generating custom sequence: {e}")
    #             return self.env['ir.sequence'].next_by_code('sale.order') or 'SO/NEW'

    #     # Generate the sale order name
    #     sale_order_name = generate_sale_order_name(business_unit)
    #     print(f"Generated sale order name: {sale_order_name}")

    #     sale_order = {
    #         'name': sale_order_name,
    #         'partner_id': self.partner_id.id,
    #         'business_unit': business_unit,
    #         'order_line': []
    #     }

    #     # Add other fields only if they exist
    #     field_mappings = [
    #         ('order_enquirey_id', self.id),
    #         ('date_order', getattr(self, 'date_order', None)),
    #         ('vessel_no', getattr(self, 'vessel_no', None)),
    #         ('imo_number', getattr(self, 'imo_number', None)),
    #         ('brand_type', getattr(self, 'brand_type', None)),
    #         ('vessel_eta', getattr(self, 'vessel_eta', None)),
    #         ('inquiry_rec_from', getattr(self, 'inquiry_rec_from', None)),
    #         ('port_note', getattr(self, 'port_note', None)),
    #         ('new_existing', getattr(self, 'new_existing', None)),
    #     ]

    #     # Add Many2one fields
    #     many2one_fields = [
    #         'delivery_by_id', 'country_port_id', 'country_id', 'delivery_type_id',
    #         'brand_master_id', 'port_master_id', 'reason_id', 'Source_of_inquiry_id',
    #         'process_stage_id'
    #     ]

    #     for field_name in many2one_fields:
    #         if hasattr(self, field_name):
    #             field_value = getattr(self, field_name)
    #             if field_value and hasattr(field_value, 'id'):
    #                 sale_order[field_name] = field_value.id

    #     # Add all other scalar fields
    #     for field_name, value in field_mappings:
    #         if value is not None:
    #             sale_order[field_name] = value

    #     # Process order lines
    #     for line in self.order_line_ids:
    #         product = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)], limit=1)
    #         if product:
    #             line_data = {
    #                 'product_id': product.id,
    #                 'name': line.name or product.name or '',
    #                 'price_unit': line.product_id.list_price or 0.0,
    #                 'product_uom_qty': getattr(line, 'product_uom_qty', 1.0),
    #                 'product_uom': line.product_uom.id if hasattr(line, 'product_uom') and line.product_uom else product.uom_id.id,
    #             }

    #             # Add optional line fields
    #             optional_line_fields = ['sequence', 'display_type', 'unit_qty']
    #             for field in optional_line_fields:
    #                 if hasattr(line, field) and getattr(line, field) is not None:
    #                     line_data[field] = getattr(line, field)

    #             # Add Many2one line fields
    #             line_many2one_fields = ['customer_ref_id', 'pack_size_id']
    #             for field in line_many2one_fields:
    #                 if hasattr(line, field):
    #                     field_value = getattr(line, field)
    #                     if field_value and hasattr(field_value, 'id'):
    #                         line_data[field] = field_value.id

    #             sale_order['order_line'].append((0, 0, line_data))

    #     print("=== CREATING SALE ORDER ===")
    #     print(f"Sale Order Data: {sale_order}")

    #     try:
    #         create_sales = self.env['sale.order'].sudo().create(sale_order)
    #         print(f"Successfully created sale order: {create_sales.name} (ID: {create_sales.id})")

    #         if create_sales:
    #             self.sale_order_id = create_sales.id
    #             self.sale_order_ids = [(4, create_sales.id)]
    #             self.state = 'convert_quote'
    #             return {
    #                 'type': 'ir.actions.act_window',
    #                 'name': 'Sales Order',
    #                 'res_model': 'sale.order',
    #                 'res_id': create_sales.id,
    #                 'view_mode': 'form',
    #                 'target': 'current',
    #             }

    #     except Exception as e:
    #         print(f"ERROR creating sale order: {str(e)}")
    #         import traceback
    #         print(f"Full traceback: {traceback.format_exc()}")
    #         raise ValidationError(f"Failed to create Sales Order: {str(e)}")

    def button_confirm(self, sales_list=None):
        if len(self.order_line_ids) <= 0:
            raise ValidationError(_("Before Confirm Please Add Product"))

        # Enhanced sequence generation with better error handling
        def generate_sequence(business_unit, sequence_type="INQ"):
            """
            Generate sequence for both inquiry and sale order
            sequence_type: 'INQ' for inquiry, 'SQ' for sale quotation
            """
            if not business_unit:
                fallback_code = (
                    "order.enquiry" if sequence_type == "INQ" else "sale.order"
                )
                fallback_default = "INQ/NEW" if sequence_type == "INQ" else "SO/NEW"
                return (
                    self.env["ir.sequence"].next_by_code(fallback_code)
                    or fallback_default
                )

            bu_prefix = get_business_unit_prefix(business_unit)

            if not bu_prefix:
                fallback_code = (
                    "order.enquiry" if sequence_type == "INQ" else "sale.order"
                )
                fallback_default = "INQ/NEW" if sequence_type == "INQ" else "SO/NEW"
                return (
                    self.env["ir.sequence"].next_by_code(fallback_code)
                    or fallback_default
                )

            try:
                from datetime import datetime

                now = datetime.now()
                month = now.strftime("%b").upper()  # MAY
                year = now.strftime("%Y")  # 2025
                sequence_code = f"{bu_prefix}-{sequence_type}-{month}-{year}"

                # Check if sequence exists, create if not
                seq = (
                    self.env["ir.sequence"]
                    .sudo()
                    .search([("code", "=", sequence_code)], limit=1)
                )
                if not seq:
                    seq_name = f'{bu_prefix} {"Inquiry" if sequence_type == "INQ" else "Sales Quotation"} {month} {year}'
                    try:
                        seq = (
                            self.env["ir.sequence"]
                            .sudo()
                            .create(
                                {
                                    "name": seq_name,
                                    "code": sequence_code,
                                    "prefix": f"{bu_prefix}-{sequence_type}-{month}-{year}-",
                                    "padding": 4,  # Reduced padding for better performance
                                    "number_next": 1,
                                    "number_increment": 1,
                                    "active": True,
                                    "implementation": "standard",
                                }
                            )
                        )
                        # Commit the sequence creation
                        self.env.cr.commit()
                    except Exception as create_error:
                        print(
                            f"Error creating sequence {sequence_code}: {create_error}"
                        )
                        # Use manual sequence generation as fallback
                        return self._generate_manual_sequence(
                            bu_prefix, sequence_type, month, year
                        )

                # Generate next number with multiple fallback methods
                try:
                    if seq:
                        # Method 1: Use sequence object directly
                        next_name = seq._next()
                        if next_name:
                            return next_name

                    # Method 2: Use next_by_code
                    next_name = (
                        self.env["ir.sequence"].sudo().next_by_code(sequence_code)
                    )
                    if next_name:
                        return next_name

                    # Method 3: Manual sequence generation
                    return self._generate_manual_sequence(
                        bu_prefix, sequence_type, month, year
                    )

                except Exception as gen_error:
                    print(
                        f"Error generating sequence from {sequence_code}: {gen_error}"
                    )
                    return self._generate_manual_sequence(
                        bu_prefix, sequence_type, month, year
                    )

            except Exception as e:
                print(f"Error in sequence generation: {e}")
                # Ultimate fallback
                fallback_code = (
                    "order.enquiry" if sequence_type == "INQ" else "sale.order"
                )
                fallback_default = "INQ/NEW" if sequence_type == "INQ" else "SO/NEW"
                return (
                    self.env["ir.sequence"].next_by_code(fallback_code)
                    or fallback_default
                )

        def _generate_manual_sequence(self, bu_prefix, sequence_type, month, year):
            """Manual sequence generation as ultimate fallback"""
            try:
                # Find the last record with similar pattern
                model_name = "order.enquiry" if sequence_type == "INQ" else "sale.order"
                pattern = f"{bu_prefix}-{sequence_type}-{month}-{year}-%"

                # Search for existing records with this pattern
                if sequence_type == "INQ":
                    last_record = self.search(
                        [("name", "like", pattern)], order="id desc", limit=1
                    )
                else:
                    last_record = (
                        self.env["sale.order"]
                        .sudo()
                        .search([("name", "like", pattern)], order="id desc", limit=1)
                    )

                if last_record and last_record.name:
                    try:
                        # Extract number from last sequence
                        last_num = int(last_record.name.split("-")[-1])
                        next_num = last_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1

                return f"{bu_prefix}-{sequence_type}-{month}-{year}-{next_num:04d}"

            except Exception as e:
                print(f"Manual sequence generation failed: {e}")
                # Final fallback with timestamp
                import time

                timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
                return f"{bu_prefix}-{sequence_type}-{month}-{year}-{timestamp}"

        # Generate and set the inquiry sequence
        business_unit = getattr(self, "business_unit", None)
        # inquiry_sequence = generate_sequence(business_unit, 'INQ')

        # Update the current inquiry record with the generated sequence
        # self.name = inquiry_sequence
        # print(f"Generated inquiry sequence: {inquiry_sequence}")

        # Generate the sale order name
        sale_order_name = generate_sequence(business_unit, "SQ")
        print(f"Generated sale order name: {sale_order_name}")

        sale_order = {
            "name": sale_order_name,
            "partner_id": self.partner_id.id,
            "business_unit": business_unit,
            "order_line": [],
        }

        # Add other fields only if they exist
        field_mappings = [
            ("order_enquirey_id", self.id),
            ("date_order", getattr(self, "date_order", None)),
            ("vessel_no", getattr(self, "vessel_no", None)),
            ("toll_sale_type", getattr(self, "toll_sale_type", None)),
            ("imo_number", getattr(self, "imo_number", None)),
            ("brand_type", getattr(self, "brand_type", None)),
            ("vessel_eta", getattr(self, "vessel_eta", None)),
            ("inquiry_rec_from", getattr(self, "inquiry_rec_from", None)),
            ("port_note", getattr(self, "port_note", None)),
            ("new_existing", getattr(self, "new_existing", None)),
            ("delivery_by_barge", getattr(self, "delivery_by_barge", None)),
            ("outside_anchorside", getattr(self, "outside_anchorside", None)),
        ]

        # Add Many2one fields
        many2one_fields = [
            "vessel_no_id",
            "imo_no_id",
            "delivery_by_id",
            "country_port_id",
            "country_id",
            "delivery_type_id",
            "brand_master_id",
            "port_master_id",
            "reason_id",
            "Source_of_inquiry_id",
            "process_stage_id",
        ]

        for field_name in many2one_fields:
            if hasattr(self, field_name):
                field_value = getattr(self, field_name)
                if field_value and hasattr(field_value, "id"):
                    sale_order[field_name] = field_value.id

        # Add all other scalar fields
        for field_name, value in field_mappings:
            if value is not None:
                sale_order[field_name] = value

        # Process order lines
        # Process order lines (order.enq lines)
        for line in self.order_line_ids:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", line.product_id.id)], limit=1
            )

            if not product:
                continue

            # Prepare line data
            if self.company_id.id == 9:
                line_data = {
                    "product_id": product.id,
                    "price_unit": line.product_id.list_price or 0.0,
                    "product_uom_qty": line.product_uom_qty or 1.0,
                    "product_uom_id": line.product_uom_id.id
                    if line.product_uom_id
                    else product.uom_id.id,
                }
            else:
                line_data = {
                    "product_id": product.id,
                    "name": line.name or product.name or "",
                    "price_unit": line.product_id.list_price or 0.0,
                    "product_uom_qty": line.product_uom_qty or 1.0,
                    "product_uom_id": line.product_uom_id.id
                    if line.product_uom_id
                    else product.uom_id.id,
                }

            # Optional simple fields
            if hasattr(line, "sequence"):
                line_data["sequence"] = line.sequence
            if hasattr(line, "display_type") and line.display_type:
                line_data["display_type"] = line.display_type
            if hasattr(line, "unit_qty"):
                line_data["unit_qty"] = line.unit_qty

            # Many2one fields
            if line.customer_ref_id:
                line_data["customer_ref_id"] = line.customer_ref_id.id
            if line.pack_size_id:
                line_data["pack_size_id"] = line.pack_size_id.id

            # -----------------------------------------------------
            # SELECT CORRECT DESTINATION BASED ON COMPANY ID
            # -----------------------------------------------------
            if self.company_id.id == 9:
                # Push into quotation lines (your custom model)
                sale_order.setdefault("quotation_lines", [])
                sale_order["quotation_lines"].append((0, 0, line_data))
            else:
                # Normal sale order lines
                sale_order.setdefault("order_line", [])
                sale_order["order_line"].append((0, 0, line_data))

        # for line in self.order_line_ids:
        #     product = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)], limit=1)
        #     if product:
        #         line_data = {
        #             'product_id': product.id,
        #             'name': line.name or product.name or '',
        #             'price_unit': line.product_id.list_price or 0.0,
        #             'product_uom_qty': getattr(line, 'product_uom_qty', 1.0),
        #             'product_uom': line.product_uom.id if hasattr(line, 'product_uom') and line.product_uom else product.uom_id.id,
        #         }

        #         # Add optional line fields
        #         optional_line_fields = ['sequence', 'display_type', 'unit_qty']
        #         for field in optional_line_fields:
        #             if hasattr(line, field) and getattr(line, field) is not None:
        #                 line_data[field] = getattr(line, field)

        #         # Add Many2one line fields
        #         line_many2one_fields = ['customer_ref_id', 'pack_size_id']
        #         for field in line_many2one_fields:
        #             if hasattr(line, field):
        #                 field_value = getattr(line, field)
        #                 if field_value and hasattr(field_value, 'id'):
        #                     line_data[field] = field_value.id

        #         sale_order['order_line'].append((0, 0, line_data))

        print("=== CREATING SALE ORDER ===")
        print(f"Sale Order Data: {sale_order}")

        try:
            create_sales = self.env["sale.order"].sudo().create(sale_order)
            print(
                f"Successfully created sale order: {create_sales.name} (ID: {create_sales.id})"
            )

            # if create_sales:
            #     self.sale_order_id = create_sales.id
            #     self.sale_order_ids = [(4, create_sales.id)]
            #     self.state = 'convert_quote'
            #     return {
            #         'type': 'ir.actions.act_window',
            #         'name': 'Sales Order',
            #         'res_model': 'sale.order',
            #         'res_id': create_sales.id,
            #         'view_mode': 'form',
            #         'target': 'current',
            #     }
            if create_sales:
                self.sale_order_id = create_sales.id
                self.sale_order_ids = [(4, create_sales.id)]
                self.state = "convert_quote"

                # Check if company is ID 9
                company = create_sales.company_id or self.env.company
                if company and company.id == 9:
                    # Get the specific form view ID
                    view_id = self.env.ref(
                        "zilancer_customisation.view_order_form_toll"
                    ).id
                    return {
                        "type": "ir.actions.act_window",
                        "name": "Sales Order",
                        "res_model": "sale.order",
                        "res_id": create_sales.id,
                        "view_mode": "form",
                        "view_id": view_id,
                        "views": [(view_id, "form")],
                        "target": "current",
                    }
                else:
                    # Existing action for other companies
                    return {
                        "type": "ir.actions.act_window",
                        "name": "Sales Order",
                        "res_model": "sale.order",
                        "res_id": create_sales.id,
                        "view_mode": "form",
                        "target": "current",
                    }

        except Exception as e:
            print(f"ERROR creating sale order: {str(e)}")
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")
            raise ValidationError(f"Failed to create Sales Order: {str(e)}")

    # def button_confirm(self, sales_list=None):
    #     if len(self.order_line_ids) <= 0:
    #         raise ValidationError(_("Before Confirm Please Add Product"))

    #     sale_order = {
    #         'partner_id': self.partner_id.id,
    #         'order_enquirey_id': self.id,
    #         'date_order': self.date_order,
    #         'order_line': []
    #     }
    #     for line in self.order_line_ids:
    #         product = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)], limit=1)
    #         order_lines = (0, 0, {
    #             'sequence': line.sequence,
    #             'product_id': product.id,
    #             'display_type': line.display_type,
    #             'name': line.name,
    #             'price_unit': line.price_unit,
    #             'product_uom': line.product_uom.id,
    #             'product_uom_qty': line.product_uom_qty,
    #             # 'tax_id': [(6, 0, line.tax_id.ids)],
    #         })
    #         sale_order['order_line'].append(order_lines)
    #     create_sales = self.env['sale.order'].create(sale_order)
    #     if create_sales:
    #         self.sale_order_id = create_sales.id
    #         self.sale_order_ids = [(4, create_sales.id)]
    #         self.state = 'confirm'

    # def view_sale_order(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Sale Order',
    #         'res_model': 'sale.order',
    #         'domain': [('id', 'in', self.sale_order_ids.ids)],
    #         'view_mode': 'list,form',
    #         'target': 'current',
    #     }
    def view_sale_order(self):
        # Check if company is ID 9
        company = self.company_id or self.env.company
        if company and company.id == 9:
            # Get the specific form view ID
            view_id = self.env.ref("zilancer_customisation.view_order_form_toll").id
            return {
                "type": "ir.actions.act_window",
                "name": "Sale Order",
                "res_model": "sale.order",
                "domain": [("id", "in", self.sale_order_ids.ids)],
                "view_mode": "list,form",
                "views": [(False, "list"), (view_id, "form")],
                "target": "current",
            }
        else:
            # Existing action for other companies
            return {
                "type": "ir.actions.act_window",
                "name": "Sale Order",
                "res_model": "sale.order",
                "domain": [("id", "in", self.sale_order_ids.ids)],
                "view_mode": "list,form",
                "target": "current",
            }

    def button_add_line_from_sales(self):
        if not self.partner_id:
            raise ValidationError("Sorry, Please Select The Customer First")
        return {
            "type": "ir.actions.act_window",
            "name": "Add Product",
            "res_model": "sale.line.wizard",
            "view_mode": "form",
            "context": {
                "customer_id": self.partner_id.id,
            },
            "target": "new",
        }

    # @api.depends_context('lang')
    # @api.depends('order_line_ids.tax_id', 'order_line_ids.price_unit', 'amount_total', 'amount_untaxed', 'currency_id')
    # def _compute_tax_totals(self):
    #     for order in self:
    #         order_lines = order.order_line_ids.filtered(lambda x: not x.display_type)
    #         order.tax_totals = self.env['account.tax']._prepare_tax_totals(
    #             [x._convert_to_tax_base_line_dict() for x in order_lines],
    #             order.currency_id or order.company_id.currency_id,
    #         )

    # @api.depends('order_line_ids.price_subtotal', 'order_line_ids.price_tax', 'order_line_ids.price_total')
    # def _compute_amounts(self):
    #     for order in self:
    #         order_lines = order.order_line_ids.filtered(lambda x: not x.display_type)

    #         if order.company_id.tax_calculation_rounding_method == 'round_globally':
    #             tax_results = self.env['account.tax']._compute_taxes([
    #                 line._convert_to_tax_base_line_dict()
    #                 for line in order_lines
    #             ])
    #             totals = tax_results['totals']
    #             amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
    #             amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
    #         else:
    #             amount_untaxed = sum(order_lines.mapped('price_subtotal'))
    #             amount_tax = sum(order_lines.mapped('price_tax'))

    #         order.amount_untaxed = amount_untaxed
    #         order.amount_tax = amount_tax
    #         order.amount_total = order.amount_untaxed + order.amount_tax


class OrderEnquiryLines(models.Model):
    _name = "order.enq.lines"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.user.company_id.id,
        string="Company",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    # product_id = fields.Many2one('product.template', string='Product', domain=[('sale_ok', '=', True)])
    product_id = fields.Many2one(
        "product.template",
        string="Product",
        domain=lambda self: [
            ("sale_ok", "=", True),
            ("company_id", "in", [self.env.company.id, False]),
        ],
    )
    price_unit = fields.Float("Unit Price")
    product_uom_qty = fields.Float("Quantity")
    product_uom_id = fields.Many2one("uom.uom", string="Unit Of Measure")
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )
    name = fields.Char("Description")
    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
    )
    enq_id = fields.Many2one("order.enq")
    # price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_amount', store=True, precompute=True)
    # price_tax = fields.Float(string="Total Tax", compute='_compute_amount', store=True, precompute=True)
    # price_total = fields.Monetary(string="Total", compute='_compute_amount', store=True, precompute=True)
    sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order ID", related="enq_id.sale_order_id"
    )
    customer_ref = fields.Char("Inquired Item")
    customer_brand = fields.Char(
        related="customer_ref_id.customer_brand", string="Customer Brand"
    )
    cust_ref_pro_category = fields.Char(
        related="customer_ref_id.cust_ref_pro_category",
        string="Cust Ref Product Category",
    )
    customer_ref_id = fields.Many2one(
        "customer.reference.master", string="Inquired Item"
    )
    pack_size_id = fields.Many2one("pack.size.master", string="Pack Size")
    unit_count_id = fields.Many2one("unit.count.master", string="No of Units")
    unit_qty = fields.Float("No of Units")

    @api.onchange("product_uom_qty", "pack_size_id")
    def _onchange_product_uom_qty(self):
        if (
            self.product_uom_qty
            and self.pack_size_id
            and self.pack_size_id.conversion_factor
        ):
            self.unit_qty = self.product_uom_qty * self.pack_size_id.conversion_factor
        else:
            self.unit_qty = 0.0

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price
            self.product_uom_id = self.product_id.uom_id.id
            # self.product_uom_qty = 1.0
            self.name = self.product_id.display_name
            self.display_type = False
            self.tax_ids = self.product_id.taxes_id

    # def _convert_to_tax_base_line_dict(self):
    #     """ Convert the current record to a dictionary in order to use the generic taxes computation method
    #     defined on account.tax.

    #     :return: A python dictionary.
    #     """
    #     self.ensure_one()
    #     return self.env['account.tax']._convert_to_tax_base_line_dict(
    #         self,
    #         partner=self.enq_id.partner_id,
    #         currency=self.enq_id.currency_id,
    #         product=self.product_id,
    #         taxes=self.tax_id,
    #         price_unit=self.price_unit,
    #         quantity=self.product_uom_qty,
    #         price_subtotal=self.price_subtotal,
    #     )

    # @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the Order Enq line.
    #     """
    #     for line in self:
    #         tax_results = self.env['account.tax'].with_company(line.company_id)._compute_taxes(
    #             [line._convert_to_tax_base_line_dict()]
    #         )
    #         totals = list(tax_results['totals'].values())[0]
    #         amount_untaxed = totals['amount_untaxed']
    #         amount_tax = totals['amount_tax']

    #         line.update({
    #             'price_subtotal': amount_untaxed,
    #             'price_tax': amount_tax,
    #             'price_total': amount_untaxed + amount_tax,
    #         })


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    order_enquirey_id = fields.Many2one(
        "order.enq", string="Order Inquiry ID", copy=False
    )
    reason_id = fields.Many2one("sale.reason", string="Reason for losing order")
    pricing = fields.Char("Pricing")
    port_issue = fields.Char("Port Issue")
    timeline_shortage = fields.Char("Timeline Shortage")
    out_of_service_area = fields.Char("Out of Service Area")
    process_stage_id = fields.Many2one("process.stage", string="Process Stage")
    new_existing = fields.Selection(
        [
            ("new", "New"),
            ("existing", "Existing"),
        ],
        string="Quotation Type",
        readonly=False,
    )
    Source_of_inquiry_id = fields.Many2one("source.inquiry", string="Source of Inquiry")
    post_tally_date = fields.Datetime(string="Posted to Tally Date Time")
    other_ref = fields.Char("Other Reference")
    dispatch_through = fields.Char("Dispatch Through")
    destination = fields.Char("Destination")
    active = fields.Boolean("Active", default=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        store=True,
        readonly=False,
        index=True,
        tracking=2,
        domain=lambda self: "[('group_ids', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ),
    )

    @api.onchange("partner_id")
    def _onchange_partners_id(self):
        if self.partner_id and not self.partner_id.user_id:
            self.user_id = False
        if self.partner_id and self.partner_id.user_id:
            self.user_id = self.partner_id.user_id

    def write(self, vals):
        res = super().write(vals)
        for order in self:
            if order.user_id and order.partner_id and not order.partner_id.user_id:
                order.partner_id.user_id = order.user_id
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.user_id and res.partner_id and not res.partner_id.user_id:
            res.partner_id.user_id = res.user_id
        return res

    def button_add_line_from_sales(self):
        if not self.partner_id:
            raise ValidationError("Sorry, Please Select The Customer First")
        return {
            "type": "ir.actions.act_window",
            "name": "Add Product",
            "res_model": "sale.line.wizard",
            "view_mode": "form",
            "context": {"customer_id": self.partner_id.id},
            "target": "new",
        }

    @api.onchange("partner_id")
    def _onchange_partner_id_check_existing_orders(self):
        for rec in self:
            if rec.partner_id:
                # Check for confirmed sale orders with at least one delivery
                sale_orders = self.env["sale.order"].search(
                    [
                        ("partner_id", "=", rec.partner_id.id),
                        ("state", "=", "sale"),  # Confirmed orders only
                        ("picking_ids", "!=", False),
                    ],
                    limit=1,
                )
                print("---sale_orders-------------", sale_orders)
                if sale_orders:
                    rec.new_existing = "existing"
                else:
                    rec.new_existing = "new"
                print("---rec.new_existing-------------", rec.new_existing)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_ref = fields.Char(string="Customer Ref")
    customer_ref_id = fields.Many2one(
        "customer.reference.master", string="Inquired Item"
    )
    pack_size_id = fields.Many2one("pack.size.master", string="Pack Size")
    unit_count_id = fields.Many2one("unit.count.master", string="No of Units")
    unit_qty = fields.Float("No of Units")
    customer_brand = fields.Char(
        related="customer_ref_id.customer_brand", string="Customer Brand"
    )
    cust_ref_pro_category = fields.Char(
        related="customer_ref_id.cust_ref_pro_category",
        string="Cust Ref Product Category",
    )
    # unit_qty = pack_size.conversion_factor * product_uom_qty


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    used_in_inquiry_or_order = fields.Boolean(
        string="Used in Inquiry or Order",
        compute="_compute_used_in_inquiry_or_order",
        store=True,
    )

    def _compute_used_in_inquiry_or_order(self):
        SaleOrderLine = self.env["sale.order.line"]
        EnquiryLine = self.env[
            "order.enq.lines"
        ]  # assuming your enquiry has lines model
        for product in self:
            product_ids = product.id  # all variants of the template
            # Check if used in sale order line
            sale_used = bool(
                SaleOrderLine.search_count(
                    [("product_template_id", "=", product_ids)], limit=1
                )
            )
            # Check if used in enquiry lines
            enq_used = bool(
                EnquiryLine.search_count([("product_id", "=", product_ids)], limit=1)
            )
            product.used_in_inquiry_or_order = sale_used or enq_used

    def button_add_sales_line(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Add Product",
            "res_model": "product.add.wizard",
            "view_mode": "form",
            "context": {
                "default_product_id": self.id,
                "default_price_unit": self.list_price,
                "default_product_uom": self.uom_id.id,
            },
            "target": "new",
        }


class ResPartner(models.Model):
    _inherit = "res.partner"

    inquiry_count = fields.Integer(
        string="Inquiry Count", compute="_compute_inquiry_count"
    )

    def _compute_inquiry_count(self):
        order_data = self.env["order.enq"].read_group(
            [("partner_id", "in", self.ids)], ["partner_id"], ["partner_id"]
        )
        mapped_data = {
            data["partner_id"][0]: data["partner_id_count"] for data in order_data
        }
        for partner in self:
            partner.inquiry_count = mapped_data.get(partner.id, 0)
