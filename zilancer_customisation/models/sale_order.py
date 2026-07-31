from odoo import models, fields, Command, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.sale_order_enquiry.business_unit_data import (
    BUSINESS_UNIT_SELECTION,
    get_business_unit_prefix,
)
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from werkzeug import urls
from odoo.tools import float_repr

SALE_ORDER_STATE = [
    ("draft", "Quotation"),
    ("sent", "Quotation Sent"),
    ("approved", "Approved"),
    ("sale", "Sales Order"),
    ("cancel", "Cancelled"),
]


class QuotationLine(models.Model):
    _name = "quotation.line"
    _description = "Quotation Line"
    _order = "sequence, id"

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order", ondelete="cascade"
    )

    sequence = fields.Integer(string="Sequence", default=10)

    product_id = fields.Many2one("product.product", string="Product", required=True)

    product_uom_qty = fields.Float(string="Qty in Units", default=1.0, required=True)

    product_uom = fields.Many2one("uom.uom", string="Unit of Measure", required=True)

    price_unit = fields.Float(string="Unit Price", digits="Product Price")

    tax_id = fields.Many2many(comodel_name="account.tax", string="Taxes")

    discount = fields.Float(string="Disc. %")

    price_subtotal = fields.Monetary(
        string="Amount", compute="_compute_subtotal", store=True
    )

    currency_id = fields.Many2one(related="order_id.currency_id", store=True)
    unit_qty = fields.Float("No of Units")
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

    @api.onchange("product_id")
    def _onchange_product_id_set_values(self):
        for line in self:
            if not line.product_id:
                return

            product = line.product_id

            # Set UoM automatically
            line.product_uom = product.uom_id.id

            # Set default price (sale price)
            line.price_unit = product.lst_price

            # Set taxes automatically
            line.tax_id = product.taxes_id

            # Reset quantity to 1
            if not line.product_uom_qty:
                line.product_uom_qty = 1

    @api.depends("product_uom_qty", "price_unit", "discount", "tax_id")
    def _compute_subtotal(self):
        for line in self:
            order = line.order_id
            if not order:
                line.price_subtotal = 0.0
                continue

            # Apply discount
            price = line.price_unit * (1 - (line.discount or 0.0) / 100)

            # Compute taxes exactly like sale.order.line
            taxes = line.tax_id.compute_all(
                price,
                quantity=line.product_uom_qty,
                currency=order.currency_id,
                product=line.product_id,
                partner=order.partner_id,
            )

            line.price_subtotal = taxes["total_included"]

    @api.onchange("product_id")
    def _onchange_product_id_pack_size(self):
        """When selecting product, auto-fill pack_size_id from product template."""
        for line in self:
            company = line.order_id.company_id or self.env.company

            # If company is ID 13 → use kgs_per_pkg_type
            if company and company.id == 13:
                if line.product_id:
                    product_tmpl = line.product_id.product_tmpl_id
                    line.pack_size_id = product_tmpl.pack_size_id.id or False
            else:
                line.pack_size_id = False

    @api.onchange("product_uom_qty", "product_id", "pack_size_id")
    def _onchange_product_uom_qty(self):
        """Compute unit_qty dynamically based on company and pack size."""
        for line in self:
            line.unit_qty = 0.0

            if not line.product_id or not line.product_uom_qty:
                continue

            product_tmpl = line.product_id.product_tmpl_id
            company = line.order_id.company_id or self.env.company

            # ✅ If company is ID 13 → use kgs_per_pkg_type
            if company and company.id == 13:
                if product_tmpl.kgs_per_pkg_type:
                    line.unit_qty = line.product_uom_qty * product_tmpl.kgs_per_pkg_type
                else:
                    line.unit_qty = 0.0
            else:
                # ✅ Otherwise use pack size conversion factor
                conversion = 0.0
                if line.pack_size_id and line.pack_size_id.conversion_factor:
                    conversion = line.pack_size_id.conversion_factor
                elif (
                    product_tmpl.pack_size_id
                    and product_tmpl.pack_size_id.conversion_factor
                ):
                    conversion = product_tmpl.pack_size_id.conversion_factor
                line.unit_qty = line.product_uom_qty * conversion


class SaleOrder(models.Model):
    _inherit = "sale.order"

    approval_remarks = fields.Text(string="Approval Remarks")
    sales_order_received = fields.Boolean(string="Sales Order Received")
    sales_order_date = fields.Date(string="Sales Order Date")
    po_received = fields.Boolean(string="PO Received")
    po_number = fields.Char(string="PO Number")
    purchase_order_date = fields.Date(string="Purchase Order Date")
    production_started = fields.Boolean(string="Production Started")
    expected_closure_date = fields.Char(string="Expected Closure Date")
    production_date = fields.Date(string="Production Date")
    expected_date_of_completion = fields.Date(string="Expected Date of Completion")
    # addition marine
    vessel_no = fields.Char(string="Vessel")
    imo_number = fields.Char(string="IMO")
    vessel_no_id = fields.Many2one("vessel.no", string="Vessel Name")
    imo_no_id = fields.Many2one("imo.number", string="IMO Number")
    delivery_by_barge = fields.Boolean(string="Delivery by Barge")
    delivery_by_id = fields.Many2one("delivery.by", string="Delivery By")
    port_name = fields.Char(string="Port Name")
    country_id = fields.Many2one("res.country", string="Country of Supply")
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
    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        default=lambda self: self.env.company.business_unit
    )
    # default=lambda self: self.env.company.business_unit
    master_brand = fields.Char(string="Master Brand")
    brand_type = fields.Char(string="Brand Type")
    vessel_eta = fields.Date(string="Vessel ETA")
    country_port_id = fields.Many2one("res.country", string="Country of Supply")
    inquiry_rec_from = fields.Char(string="Inquiry Received From")
    brand_master_id = fields.Many2one("brand.master", string="Master Brand")
    port_master_id = fields.Many2one("port.master", string="Port Name")
    port_note = fields.Html("Notes")
    vessel_agent_name = fields.Char(string="Vessel Agent Name")
    contact_details = fields.Char(string="Contact Details")
    delivery_special_instructions = fields.Html(
        string="Special instructions for the delivery"
    )
    operational_status = fields.Selection(
        [("present", "Present"), ("not_present", "Not Present")],
        string="Operational Status @ Port",
        default="present",
    )
    total_quantity = fields.Float(
        compute="_compute_total_quantity", string="Total Quantity"
    )
    total_qty_units = fields.Float(
        compute="_compute_total_qty_units", string="Total Qty in L"
    )
    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )
    sale_quotes = fields.Integer(string="Sale Quotes")
    sale_orders = fields.Integer(string="Sale Orders")
    total_quotes = fields.Integer(
        compute="_compute_total_quotes", string="Total Quotes"
    )
    total_orders = fields.Integer(
        compute="_compute_total_quotes", string="Total Orders"
    )
    adnoc_ids = fields.One2many("adnoc.stage", "sale_id", string="Adnoc Lines")
    automotive_ids = fields.One2many(
        "automotive.stage", "sale_id", string="Automotive Lines"
    )
    amendment_ids = fields.One2many(
        "amendment.amendment", "sale_id", string="Amendment"
    )

    vat_selection = fields.Selection(
        [
            ("vat_5", "VAT - 5%"),
            ("vat_0", "VAT - 0%"),
            ("vat_not_applicable", "VAT - Not Applicable"),
        ],
        string="VAT",
    )
    sale_type = fields.Selection(
        [("local_sale", "Local Sales"), ("out_of_scope", "Out of Scope")],
        string="Sale Type",
    )
    customer_user_id = fields.Many2one(
        related="partner_id.user_id", string="Customer Sales Person", store=True
    )
    toll_sale_type = fields.Selection(
        [("rm", "Raw Material"), ("fg", "Finished Goods")], string="Sale Type"
    )
    client_po_order_no = fields.Char(string="Client PO Order No")
    quotation_lines = fields.One2many(
        comodel_name="quotation.line", inverse_name="order_id", string="Quotation Lines"
    )
    # quotation_lines = fields.One2many(
    #     'sale.order.line',
    #     'quotation_order_id',
    #     string='Quotation Lines', copy=True, auto_join=True
    # )

    quote_amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        store=True,
        compute="_compute_quotation_amounts",
        tracking=5,
    )
    quote_amount_tax = fields.Monetary(
        string="Taxes", store=True, compute="_compute_quotation_amounts"
    )
    quote_amount_total = fields.Monetary(
        string="Total", store=True, compute="_compute_quotation_amounts", tracking=4
    )

    show_total = fields.Boolean(string="Show Total", default=True)

    def action_confirm(self):
        for order in self:
            if order.company_id.id == 9:
                order._create_sale_lines_from_quotation()

        return super(SaleOrder, self).action_confirm()

    def _create_sale_lines_from_quotation(self):
        for order in self:
            if not order.quotation_lines:
                continue

            # Optional: Clear existing order lines before inserting
            order.order_line.unlink()

            for qline in order.quotation_lines:
                vals = {
                    "order_id": order.id,
                    "sequence": qline.sequence,
                    "product_id": qline.product_id.id,
                    "product_uom_qty": qline.product_uom_qty,
                    "product_uom_id": qline.product_uom.id,
                    "price_unit": qline.price_unit,
                    "discount": qline.discount,
                    "tax_ids": [(6, 0, qline.tax_id.ids)],
                    "name": qline.product_id.name or "",
                    # Extra custom fields
                    "unit_qty": qline.unit_qty,
                    "customer_brand": qline.customer_brand,
                    "cust_ref_pro_category": qline.cust_ref_pro_category,
                    "customer_ref_id": qline.customer_ref_id.id,
                    "pack_size_id": qline.pack_size_id.id,
                }

                self.env["sale.order.line"].create(vals)

    @api.depends("quotation_lines")
    def _compute_quotation_amounts(self):
        """Compute quotation amounts with tax and discount"""
        for order in self:
            lines = order.quotation_lines

            if not lines:
                order.update(
                    {
                        "quote_amount_untaxed": 0,
                        "quote_amount_tax": 0,
                        "quote_amount_total": 0,
                    }
                )
                continue

            # Initialize
            untaxed = 0.0
            tax = 0.0
            total = 0.0

            for line in lines:
                # Calculate price after discount
                price_after_discount = line.price_unit * (
                    1 - (line.discount or 0.0) / 100.0
                )

                # Compute taxes
                taxes = line.tax_id.compute_all(
                    price_after_discount,
                    order.currency_id,
                    line.product_uom_qty,
                    product=line.product_id,
                    partner=order.partner_id,
                )

                # Add to totals
                untaxed += taxes["total_excluded"]
                tax += taxes["total_included"] - taxes["total_excluded"]
                total += taxes["total_included"]

            # Assign values
            order.quote_amount_untaxed = untaxed
            order.quote_amount_tax = tax
            order.quote_amount_total = total

    @api.depends(
        "order_line.discount_value",
        "order_line.tax_ids",
        "currency_id",
        "company_id",
        "payment_term_id",
    )
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            currency = order.currency_id or order.company_id.currency_id

            for line in order.order_line.filtered(lambda l: not l.display_type):
                # Use discounted value for subtotal
                line_subtotal = (line.price_subtotal - line.discount_value) or 0.0
                qty = line.product_uom_qty or 1.0
                price_unit = line_subtotal / qty if qty else 0.0

                # Add to untaxed total
                amount_untaxed += line_subtotal

                # Compute tax based on discounted value
                taxes = line.tax_ids.compute_all(
                    price_unit,
                    currency,
                    qty,
                    product=line.product_id,
                    partner=order.partner_shipping_id,
                )
                amount_tax += taxes["total_included"] - taxes["total_excluded"]

            # Set order totals
            order.amount_untaxed = currency.round(amount_untaxed)
            order.amount_tax = currency.round(amount_tax)
            order.amount_total = order.amount_untaxed + order.amount_tax

    @api.onchange("vessel_no_id")
    def _onchange_vessel_no_id(self):
        if self.vessel_no_id and self.vessel_no_id.imo_number:
            self.imo_number = self.vessel_no_id.imo_number

    @api.depends("company_id")
    def _compute_validity_date(self):
        today = fields.Date.context_today(self)
        for order in self:
            days = 7
            if days > 0:
                order.validity_date = today + timedelta(days)
            else:
                order.validity_date = False

    @api.onchange("vat_selection")
    def onchange_vat_selection(self):
        if self.vat_selection and self.order_line:
            # Define tax names based on VAT selection
            tax_names = {"vat_5": "5% AD", "vat_0": "0%", "vat_not_applicable": None}
            tax_name = tax_names.get(self.vat_selection)
            tax_id = None
            if tax_name:
                # Search for tax by name
                tax_id = self.env["account.tax"].search(
                    [
                        ("name", "=", tax_name),
                        ("type_tax_use", "=", "sale"),
                        # ('company_id', '=', self.company_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
            # Update all order lines with the selected tax
            for line in self.order_line:
                if self.vat_selection == "vat_not_applicable" or not tax_id:
                    line.tax_ids = [(5, 0, 0)]  # Remove all taxes
                else:
                    line.tax_ids = [(6, 0, [tax_id.id])]  # Set the tax

            for line in self.quotation_lines:
                if self.vat_selection == "vat_not_applicable" or not tax_id:
                    line.tax_id = [(5, 0, 0)]  # Remove all taxes
                else:
                    line.tax_id = [(6, 0, [tax_id.id])]  # Set the tax

    def action_unlock(self):
        """Override to open the amendment wizard instead of directly unlocking"""
        return {
            "name": "Amendment Details",
            "type": "ir.actions.act_window",
            "res_model": "sale.order.amendment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_sale_order_id": self.id},
        }

    @api.onchange("port_master_id")
    def onchange_port_master_id(self):
        if self.port_master_id:
            self.country_port_id = self.port_master_id.country_id.id
            self.port_note = self.port_master_id.note

    @api.constrains("order_line")
    def _check_non_zero_price(self):
        for order in self:
            for line in order.order_line.filtered(lambda dis: not dis.display_type):
                if (
                    line.product_id.name != "Discount"
                    and line.price_unit <= 0
                    and line.product_id.default_code != "S-NOT"
                ):
                    raise ValidationError(
                        f"The product '{line.product_id.display_name}' has a price of 0. "
                        "Please set a valid price before saving the quotation."
                    )

    def action_custom_cancel(self):
        self._action_cancel()

    def _compute_total_quotes(self):
        quote_ids = self.search([("state", "not in", ["sale", "cancel"])])
        order_ids = self.search(
            [("state", "in", ["draft", "sent", "cancel", "approved"])]
        )
        for rec in self:
            rec.total_quotes = len(quote_ids) or 0
            rec.total_orders = len(order_ids) or 0

    @api.model
    def _is_sale_order_new_name(self, name):
        """Return True when the SO name still needs BU-based numbering."""
        return not name or name in ("New", _("New"), "/")

    @api.model
    def _get_business_unit_for_vals(self, vals):
        """Resolve business unit from vals or the target company."""
        business_unit = vals.get("business_unit")
        if business_unit:
            return business_unit
        company = self.env["res.company"].browse(
            vals.get("company_id") or self.env.company.id
        )
        return company.business_unit

    @api.model
    def _generate_business_unit_sequence_name(self, business_unit, sequence_type="SQ"):
        """Generate the next document number for a business unit."""
        if not business_unit:
            raise UserError(_("Business Unit is required to generate the sequence."))

        bu_prefix = get_business_unit_prefix(business_unit)
        if not bu_prefix:
            raise UserError(_("Invalid business unit: %s") % business_unit)

        now = datetime.now()
        month = now.strftime("%b").upper()
        year = now.strftime("%Y")
        sequence_code = f"{bu_prefix}-{sequence_type}-{month}-{year}"

        seq = (
            self.env["ir.sequence"]
            .sudo()
            .search([("code", "=", sequence_code)], limit=1)
        )
        if not seq:
            try:
                seq = self.env["ir.sequence"].sudo().create(
                    {
                        "name": sequence_code,
                        "code": sequence_code,
                        "prefix": f"{bu_prefix}-{sequence_type}-{month}-{year}-",
                        "padding": 4,
                        "number_next": 1,
                        "number_increment": 1,
                        "active": True,
                        "implementation": "standard",
                    }
                )
            except Exception as e:
                raise UserError(
                    _("Failed to create sequence %(code)s: %(error)s")
                    % {"code": sequence_code, "error": str(e)}
                ) from e

        try:
            next_name = seq._next() if seq else False
            if not next_name:
                next_name = self.env["ir.sequence"].sudo().next_by_code(sequence_code)
            if not next_name:
                next_name = self._generate_manual_business_unit_sequence_name(
                    bu_prefix, sequence_type, month, year
                )
            return next_name
        except Exception as e:
            raise UserError(
                _("Failed to generate sequence for code %(code)s: %(error)s")
                % {"code": sequence_code, "error": str(e)}
            ) from e

    @api.model
    def _generate_manual_business_unit_sequence_name(
        self, bu_prefix, sequence_type, month, year
    ):
        """Fallback numbering when ir.sequence is unavailable."""
        last_order = (
            self.env["sale.order"]
            .sudo()
            .search(
                [("name", "like", f"{bu_prefix}-{sequence_type}-{month}-{year}-%")],
                order="id desc",
                limit=1,
            )
        )
        if last_order and last_order.name:
            try:
                next_num = int(last_order.name.split("-")[-1]) + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        return f"{bu_prefix}-{sequence_type}-{month}-{year}-{next_num:04d}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self._is_sale_order_new_name(vals.get("name")):
                continue

            business_unit = self._get_business_unit_for_vals(vals)
            vals["business_unit"] = business_unit
            vals["name"] = self._generate_business_unit_sequence_name(
                business_unit, "SQ"
            )

        return super().create(vals_list)

    def _compute_total_qty_units(self):
        for rec in self:
            rec.total_qty_units = (
                sum(
                    rec.order_line.filtered(
                        lambda l: l.product_id.name != "Discount"
                        or not l.product_id.is_expences
                    ).mapped("unit_qty")
                )
                or 0
            )

    # @api.depends('vessel_eta')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_quantity = (
                sum(
                    rec.order_line.filtered(
                        lambda l: l.product_id.name != "Discount"
                        or not l.product_id.is_expences
                    ).mapped("product_uom_qty")
                )
                or 0
            )

    def action_request_approval(self):
        """Opens the approval wizard when the approval button is clicked."""
        return {
            "type": "ir.actions.act_window",
            "name": "Approve Sale Order",
            "res_model": "sale.order.approval.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_sale_order_id": self.id},
        }

    def _confirmation_error_message(self):
        """Return whether order can be confirmed or not if not then returm error message."""
        self.ensure_one()
        if self.state not in {"draft", "sent", "approved"}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
            not line.display_type and not line.is_downpayment and not line.product_id
            for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    def action_approve_order(self, remarks):
        """Approves the order and updates the remarks field"""
        self.write({"approval_remarks": remarks, "state": "approved"})
        # self.action_confirm()

    container_allocation_ids = fields.One2many(
        "sale.container.allocation", "sale_order_id", string="Container Allocation"
    )

    @api.onchange("order_line")
    def _compute_container_allocation(self):
        """Auto-allocate containers based on total weight"""
        total_weight = sum(self.order_line.mapped("total_weight"))
        container_types = self.env["container.master"].search(
            [], order="weight_capacity desc"
        )

        allocated_containers = []
        remaining_weight = total_weight

        for container in container_types:
            if remaining_weight <= 0:
                break

            qty = remaining_weight // container.weight_capacity
            if qty > 0:
                allocated_containers.append(
                    (
                        0,
                        0,
                        {
                            "container_id": container.id,
                            "quantity": int(qty),
                            "total_capacity": container.weight_capacity * qty,
                        },
                    )
                )
                remaining_weight -= qty * container.weight_capacity

        self.container_allocation_ids = allocated_containers

    @api.constrains("order_line", "container_allocation_ids")
    def _check_weight_capacity(self):
        """Validation to prevent overloading containers"""
        if self.container_allocation_ids:
            total_weight = sum(self.order_line.mapped("total_weight"))
            total_capacity = sum(self.container_allocation_ids.mapped("total_capacity"))
            if total_weight > total_capacity:
                raise ValidationError(
                    "Total item weight exceeds available container capacity! Adjust container allocation."
                )

    @api.onchange("sale_type")
    def _onchange_sale_type(self):
        for order in self:
            if order.sale_type == "out_of_scope":
                # Reset purchase price and margin on all lines
                order.order_line.update(
                    {
                        "purchase_price": 0.0,
                        "margin_value": 0.0,
                    }
                )
            elif order.sale_type == "local_sale":
                # Reset offered price and discount fields on all lines
                order.order_line.update(
                    {
                        "offered_price": 0.0,
                        "discount_rate": 0.0,
                        "discount_value": 0.0,
                    }
                )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    weight_per_unit = fields.Float(
        related="product_id.weight", string="Weight per Unit (kg)", store=True
    )
    total_weight = fields.Float(
        string="Total Weight", compute="_compute_total_weight", store=True
    )

    offered_price = fields.Float("Offered Price")
    # discount_rate = fields.Float("Discount")
    # discount_value = fields.Float("Discount Value")

    purchase_price = fields.Float("Purchase Price")
    margin_value = fields.Float("Margin")
    hs_code = fields.Char("HS Code")
    # profit_value = fields.Float("Profit Value")
    leads_time = fields.Char("Lead Time")
    quotation_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Quotation Order",
        ondelete="cascade",
        index=True,
        copy=False,
    )
    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )

    sale_type_line = fields.Selection(
        related="order_id.sale_type", string="Sale Type", store=True, readonly=True
    )
    discount_rate = fields.Float(
        string="Discount",
        compute="_compute_discount_fields",
        store=True,
        help="Discount rate calculated from unit price and offered price",
    )
    discount_value = fields.Float(
        string="Discount Value",
        compute="_compute_discount_fields",
        store=True,
        help="Total discount value (discount_rate * quantity)",
    )
    profit_value = fields.Float(
        "Profit Value", compute="_compute_profit_value", store=True
    )

    @api.depends("product_id", "linked_line_id", "linked_line_ids")
    def _compute_name(self):
        for line in self:
            if not line.product_id and not line.is_downpayment:
                continue

            lang = line.order_id._get_lang() if line.order_id else False
            if lang != self.env.lang:
                line = line.with_context(lang=lang)

            if line.product_id:
                line.name = line._get_sale_order_line_multiline_description_sale()
                continue

            if line.is_downpayment:
                line.name = line._get_downpayment_description()

    def _prepare_procurement_values(self):
        """Pass sale line product notes to delivery move Dispatch Instructions."""
        values = super()._prepare_procurement_values()
        self.ensure_one()
        if self.display_type or self.is_downpayment:
            return values
        # Line description / notes (product name + any extra notes on the line)
        if self.name:
            values['remarks'] = self.name
        return values

    @api.depends("purchase_price", "margin_value", "product_uom_qty", "unit_qty")
    def _compute_profit_value(self):
        """Compute profit value based on margin and quantity"""
        for line in self:
            if line.margin_value and line.product_uom_qty:
                line.profit_value = line.margin_value * line.product_uom_qty
            else:
                line.profit_value = 0.0

    @api.depends("price_unit", "offered_price", "product_uom_qty", "unit_qty")
    def _compute_discount_fields(self):
        for record in self:
            if record.price_unit and record.offered_price:
                # Calculate discount rate: difference between unit price and offered price
                record.discount_rate = record.price_unit - record.offered_price
                # Calculate discount value: discount rate * quantity
                record.discount_value = record.discount_rate * record.product_uom_qty
            else:
                record.discount_rate = 0.0
                record.discount_value = 0.0

    @api.depends("product_uom_qty", "weight_per_unit", "product_id")
    def _compute_total_weight(self):
        for line in self:
            line.total_weight = line.product_uom_qty * line.weight_per_unit

    # unit_qty = pack_size.conversion_factor * product_uom_qty
    # @api.onchange('product_uom_qty', 'pack_size_id')
    # def _onchange_product_uom_qty(self):
    #     if self.product_uom_qty and self.pack_size_id and self.pack_size_id.conversion_factor:
    #         self.unit_qty = self.product_uom_qty * self.pack_size_id.conversion_factor
    #     else:
    #         self.unit_qty = 0.0

    @api.onchange("product_id")
    def _onchange_product_id_pack_size(self):
        """When selecting product, auto-fill pack_size_id from product template."""
        for line in self:
            company = line.order_id.company_id or self.env.company

            # If company is ID 13 → use kgs_per_pkg_type
            if company and company.id == 13:
                if line.product_id:
                    product_tmpl = line.product_id.product_tmpl_id
                    line.pack_size_id = product_tmpl.pack_size_id.id or False
            else:
                line.pack_size_id = False

    @api.onchange("product_uom_qty", "product_id", "pack_size_id")
    def _onchange_product_uom_qty(self):
        """Compute unit_qty dynamically based on company and pack size."""
        for line in self:
            line.unit_qty = 0.0

            if not line.product_id or not line.product_uom_qty:
                continue

            product_tmpl = line.product_id.product_tmpl_id
            company = line.order_id.company_id or self.env.company

            # ✅ If company is ID 13 → use kgs_per_pkg_type
            if company and company.id == 13:
                if product_tmpl.kgs_per_pkg_type:
                    line.unit_qty = line.product_uom_qty * product_tmpl.kgs_per_pkg_type
                else:
                    line.unit_qty = 0.0
            else:
                # ✅ Otherwise use pack size conversion factor
                conversion = 0.0
                if line.pack_size_id and line.pack_size_id.conversion_factor:
                    conversion = line.pack_size_id.conversion_factor
                elif (
                    product_tmpl.pack_size_id
                    and product_tmpl.pack_size_id.conversion_factor
                ):
                    conversion = product_tmpl.pack_size_id.conversion_factor
                line.unit_qty = line.product_uom_qty * conversion

    @api.onchange("purchase_price", "margin_value", "product_uom_qty", "unit_qty")
    def onchange_purchase_price(self):
        """Update price_unit based on purchase_price and margin_value"""
        for line in self:
            if line.purchase_price and line.margin_value:
                # Calculate price_unit = purchase_price + margin_value
                line.price_unit = line.purchase_price + line.margin_value
            elif line.purchase_price and not line.margin_value:
                # If only purchase price is set, use it as price_unit
                line.price_unit = line.purchase_price
            # Trigger profit value calculation
            line._compute_profit_value()


class SaleOrderDiscount(models.TransientModel):
    _inherit = "sale.order.discount"

    discount_type = fields.Selection(
        selection=[
            ("sol_discount", "On All Order Lines"),
            ("so_discount", "Discount %"),
            ("amount", "Lumsum Disc"),
        ],
        default="sol_discount",
    )

    def _create_discount_lines(self):
        """Create SOline(s) according to wizard configuration"""
        self.ensure_one()
        discount_product = self._get_discount_product()
        if self.discount_type == "amount":
            if self.discount_type == "amount":
                if not self.sale_order_id.amount_total:
                    return
                so_amount = self.sale_order_id.amount_total
                # Fixed taxes cannot be discounted, so they cannot be considered in the total amount
                # when computing the discount percentage.
                if any(
                    tax.amount_type == "fixed"
                    for tax in self.sale_order_id.order_line.tax_ids.flatten_taxes_hierarchy()
                ):
                    fixed_taxes_amount = 0
                    for line in self.sale_order_id.order_line:
                        taxes = line.tax_ids.flatten_taxes_hierarchy()
                        for tax in taxes.filtered(
                            lambda tax: tax.amount_type == "fixed"
                        ):
                            fixed_taxes_amount += tax.amount * line.product_uom_qty
                    so_amount -= fixed_taxes_amount
                discount_percentage = self.discount_amount / so_amount
            else:  # so_discount
                discount_percentage = self.discount_percentage
            total_price_per_tax_groups = defaultdict(float)
            for line in self.sale_order_id.order_line:
                if not line.product_uom_qty or not line.price_unit:
                    continue
                # Fixed taxes cannot be discounted.
                taxes = line.tax_ids.flatten_taxes_hierarchy()
                fixed_taxes = taxes.filtered(lambda t: t.amount_type == "fixed")
                taxes -= fixed_taxes
                total_price_per_tax_groups[taxes] += (
                    line.price_unit
                    * (1 - (line.discount or 0.0) / 100)
                    * line.product_uom_qty
                )

            discount_dp = self.env["decimal.precision"].precision_get("Discount")
            context = {"lang": self.sale_order_id._get_lang()}  # noqa: F841
            if not total_price_per_tax_groups:
                # No valid lines on which the discount can be applied
                return
            if len(total_price_per_tax_groups) == 1:
                # No taxes, or all lines have the exact same taxes
                taxes = next(iter(total_price_per_tax_groups.keys()))
                subtotal = total_price_per_tax_groups[taxes]
                vals_list = [
                    {
                        **self._prepare_discount_line_values(
                            product=discount_product,
                            amount=self.discount_amount,
                            taxes=False,
                            description=_(
                                "Discount %(percent)s%%",
                                percent=float_repr(
                                    discount_percentage * 100, discount_dp
                                ),
                            ),
                        ),
                    }
                ]
            else:
                vals_list = []
                for taxes, subtotal in total_price_per_tax_groups.items():
                    discount_line_value = self._prepare_discount_line_values(
                        product=discount_product,
                        amount=self.discount_amount,
                        taxes=taxes,
                        description=_(
                            "Discount %(percent)s%%"
                            "- On products with the following taxes %(taxes)s",
                            percent=float_repr(discount_percentage * 100, discount_dp),
                            taxes=", ".join(taxes.mapped("name")),
                        )
                        if self.discount_type != "amount"
                        else _(
                            "Discount"
                            "- On products with the following taxes %(taxes)s",
                            taxes=", ".join(taxes.mapped("name")),
                        ),
                    )
                    vals_list.append(discount_line_value)
            return self.env["sale.order.line"].create(vals_list)
        else:
            if self.discount_type == "amount":
                if not self.sale_order_id.amount_total:
                    return
                so_amount = self.sale_order_id.amount_total
                # Fixed taxes cannot be discounted, so they cannot be considered in the total amount
                # when computing the discount percentage.
                if any(
                    tax.amount_type == "fixed"
                    for tax in self.sale_order_id.order_line.tax_ids.flatten_taxes_hierarchy()
                ):
                    fixed_taxes_amount = 0
                    for line in self.sale_order_id.order_line:
                        taxes = line.tax_ids.flatten_taxes_hierarchy()
                        for tax in taxes.filtered(
                            lambda tax: tax.amount_type == "fixed"
                        ):
                            fixed_taxes_amount += tax.amount * line.product_uom_qty
                    so_amount -= fixed_taxes_amount
                discount_percentage = self.discount_amount / so_amount
            else:  # so_discount
                discount_percentage = self.discount_percentage
            total_price_per_tax_groups = defaultdict(float)
            for line in self.sale_order_id.order_line:
                if not line.product_uom_qty or not line.price_unit:
                    continue
                # Fixed taxes cannot be discounted.
                taxes = line.tax_ids.flatten_taxes_hierarchy()
                fixed_taxes = taxes.filtered(lambda t: t.amount_type == "fixed")
                taxes -= fixed_taxes
                total_price_per_tax_groups[taxes] += (
                    line.price_unit
                    * (1 - (line.discount or 0.0) / 100)
                    * line.product_uom_qty
                )

            discount_dp = self.env["decimal.precision"].precision_get("Discount")
            context = {"lang": self.sale_order_id._get_lang()}  # noqa: F841
            if not total_price_per_tax_groups:
                # No valid lines on which the discount can be applied
                return
            if len(total_price_per_tax_groups) == 1:
                # No taxes, or all lines have the exact same taxes
                taxes = next(iter(total_price_per_tax_groups.keys()))
                subtotal = total_price_per_tax_groups[taxes]
                vals_list = [
                    {
                        **self._prepare_discount_line_values(
                            product=discount_product,
                            amount=subtotal * discount_percentage,
                            taxes=False,
                            description=_(
                                "Discount %(percent)s%%",
                                percent=float_repr(
                                    discount_percentage * 100, discount_dp
                                ),
                            ),
                        ),
                    }
                ]
            else:
                vals_list = []
                for taxes, subtotal in total_price_per_tax_groups.items():
                    discount_line_value = self._prepare_discount_line_values(
                        product=discount_product,
                        amount=subtotal * discount_percentage,
                        taxes=taxes,
                        description=_(
                            "Discount %(percent)s%%"
                            "- On products with the following taxes %(taxes)s",
                            percent=float_repr(discount_percentage * 100, discount_dp),
                            taxes=", ".join(taxes.mapped("name")),
                        )
                        if self.discount_type != "amount"
                        else _(
                            "Discount"
                            "- On products with the following taxes %(taxes)s",
                            taxes=", ".join(taxes.mapped("name")),
                        ),
                    )
                    vals_list.append(discount_line_value)
            return self.env["sale.order.line"].create(vals_list)

    def _prepare_discount_line_values(self, product, amount, taxes, description=None):
        self.ensure_one()

        vals = {
            "order_id": self.sale_order_id.id,
            "product_id": product.id,
            "sequence": 999,
            "price_unit": -amount,
            # 'tax_id': [Command.set(taxes.ids)],
        }
        if description:
            # If not given, name will fallback on the standard SOL logic (cf. _compute_name)
            vals["name"] = description

        return vals


class LinkTracker(models.Model):
    _inherit = "link.tracker"

    def _compute_short_url_host(self):
        for tracker in self:
            # tracker.short_url_host = tracker.get_base_url() + '/r/'
            tracker.short_url_host = tracker.url or ""

    @api.depends("code")
    def _compute_short_url(self):
        for tracker in self:
            tracker.short_url = urls.url_join(tracker.short_url_host or "", "")
