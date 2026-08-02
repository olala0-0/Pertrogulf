# -*- coding: utf-8 -*-
"""
Production Blend Sheet extensions for Bill of Materials.

Reuse existing:
  Product Name     -> product_tmpl_id
  Packaging        -> product_uom_id
  Total Qty (Kgs)  -> bom product_qty
  Item             -> line product_id
  Qty in KG        -> line product_qty

Component formulas (Excel):
  Qty in KG  = Total Qty (Kgs) * Percentage
  If no percentage set: equal split (Total / number of lines)
  Qty in Ltr = product_qty / Density

Total Qty (Liters) = SUM of component Qty in Ltr
Percentage total must not exceed 100% (sum of fractions <= 1.0)
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Ketal No = Work Center
    ketal_no = fields.Many2one(
        'mrp.workcenter',
        string='Ketal No',
        help='Machine / workcenter.',
    )
    previous_product = fields.Many2one(
        'product.product',
        string='Previous Product',
    )
    flushing_required = fields.Selection(
        [('yes', 'Y'), ('no', 'N')],
        string='Flushing Required',
    )
    flushing_qty = fields.Float(string='Flushing Qty', digits='Product Unit')

    batch_start_time = fields.Datetime(string='Batch Start Time')
    batch_stop_time = fields.Datetime(string='Batch Stop Time')
    heating_start_time = fields.Datetime(string='Heating Start Time')
    mixing_start_time = fields.Datetime(string='Mixing Start Time')
    mixing_temperature = fields.Float(string='Mixing Temperature')
    sample_given_time = fields.Datetime(string='Sample Given Time')
    batch_approval_time = fields.Datetime(string='Batch Approval Time')

    density = fields.Float(string='Density', digits=(16, 4))

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
        ],
        string='Status',
        default='draft',
        copy=False,
        required=True,
    )
    # Version tracking: auto-incremented on duplicate; shown in MRP form
    bom_version = fields.Integer(
        string='Version',
        default=1,
        copy=False,
        help='BOM version number. Auto-incremented when this BOM is duplicated.',
    )
    # Lot/Serial No: manually entered here and pulled into Manufacturing Order
    lot_number = fields.Char(
        string='Lot / Serial No',
        copy=False,
        help='Manual Lot/Serial number. Pulled into the Manufacturing Order '
             'when this BOM is selected.',
    )
    qc_control_ids = fields.One2many(
        'mrp.bom.qc.control',
        'bom_id',
        string='QC Controls',
        copy=True,
    )

    # Sum of components Qty in Ltr
    total_qty_liters = fields.Float(
        string='Total Qty (Liters)',
        compute='_compute_total_qty_liters',
        digits='Product Unit',
        help='Sum of all component Qty in Ltr.',
    )
    total_component_qty_kg = fields.Float(
        string='Total Components (KG)',
        compute='_compute_component_totals',
        digits='Product Unit',
    )
    total_component_qty_ltr = fields.Float(
        string='Total Components (Ltr)',
        compute='_compute_component_totals',
        digits='Product Unit',
    )

    @api.depends('bom_line_ids.qty_ltr')
    def _compute_total_qty_liters(self):
        for bom in self:
            bom.total_qty_liters = sum(bom.bom_line_ids.mapped('qty_ltr'))

    @api.depends('bom_line_ids.product_qty', 'bom_line_ids.qty_ltr')
    def _compute_component_totals(self):
        for bom in self:
            bom.total_component_qty_kg = sum(bom.bom_line_ids.mapped('product_qty'))
            bom.total_component_qty_ltr = sum(bom.bom_line_ids.mapped('qty_ltr'))

    def _update_component_qtys_from_total(self):
        """
        Distribute Total Qty (Kgs) across all component lines.

        - If percentages are set: Qty in KG = Total × Percentage (Excel)
        - If no percentages: equal split, e.g. 60 kg / 2 lines = 30 kg each
          and percentage is set to 1/n so total stays 100%.
        """
        for bom in self:
            lines = bom.bom_line_ids
            if not lines:
                continue
            total_kgs = bom.product_qty or 0.0
            line_count = len(lines)
            pct_total = sum(lines.mapped('percentage'))

            if float_compare(pct_total, 0.0, precision_digits=5) > 0:
                # Use entered percentages (Excel formula)
                for line in lines:
                    line.product_qty = total_kgs * (line.percentage or 0.0)
            else:
                # Equal distribute when percentage not set yet
                qty_each = total_kgs / line_count
                pct_each = 1.0 / line_count
                for line in lines:
                    line.percentage = pct_each
                    line.product_qty = qty_each

    @api.onchange('product_qty')
    def _onchange_product_qty_blend(self):
        """When Total Qty (Kgs) changes on blend sheet, distribute qty to components."""
        if not self.env.context.get('production_blend_sheet'):
            return
        self._update_component_qtys_from_total()

    @api.onchange('bom_line_ids')
    def _onchange_bom_line_ids_percentage(self):
        if not self.env.context.get('production_blend_sheet'):
            return
        total = sum(self.bom_line_ids.mapped('percentage'))
        if float_compare(total, 1.0, precision_digits=5) > 0:
            return {
                'warning': {
                    'title': _('Percentage Limit'),
                    'message': _(
                        'Total component percentage cannot exceed 100%% '
                        '(currently %.2f%%).'
                    ) % (total * 100.0),
                }
            }

    @api.constrains('bom_line_ids')
    def _check_percentage_total(self):
        # Only enforce when any line uses blend percentage
        for bom in self:
            percentages = bom.bom_line_ids.mapped('percentage')
            if not any(percentages):
                continue
            total = sum(percentages)
            if float_compare(total, 1.0, precision_digits=5) > 0:
                raise ValidationError(_(
                    'Total component percentage cannot exceed 100%% '
                    '(currently %.2f%%).'
                ) % (total * 100.0))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Auto-set bom_version to (max existing version for that product) + 1
        when creating a new BOM, so each record for the same product gets
        a unique, incrementing version number.
        """
        for vals in vals_list:
            if not vals.get('bom_version') and vals.get('product_tmpl_id'):
                max_v = max(
                    self.search([
                        ('product_tmpl_id', '=', vals['product_tmpl_id'])
                    ]).mapped('bom_version') or [0]
                )
                vals['bom_version'] = max_v + 1
        return super().create(vals_list)

    def copy(self, default=None):
        """
        When duplicating a BOM / Blendsheet, automatically assign the next
        version number for the same product template.
        """
        default = dict(default or {})
        if 'bom_version' not in default:
            max_v = max(
                self.search([
                    ('product_tmpl_id', '=', self.product_tmpl_id.id)
                ]).mapped('bom_version') or [0]
            )
            default['bom_version'] = max_v + 1
        return super().copy(default)

    def write(self, vals):
        res = super().write(vals)
        if 'product_qty' in vals and not self.env.context.get('skip_blend_sync'):
            for bom in self:
                lines = bom.bom_line_ids
                if not lines:
                    continue
                total_kgs = bom.product_qty or 0.0
                pct_total = sum(lines.mapped('percentage'))
                # Scale by percentage when blend % is set (safe for blend records)
                if float_compare(pct_total, 0.0, precision_digits=5) > 0:
                    for line in lines:
                        qty_kg = total_kgs * (line.percentage or 0.0)
                        line.with_context(skip_blend_sync=True).write({
                            'product_qty': qty_kg,
                        })
                # Equal split only from Production Blend Sheet menu
                elif self.env.context.get('production_blend_sheet'):
                    line_count = len(lines)
                    qty_each = total_kgs / line_count
                    pct_each = 1.0 / line_count
                    for line in lines:
                        line.with_context(skip_blend_sync=True).write({
                            'percentage': pct_each,
                            'product_qty': qty_each,
                        })
        return res

    def button_approve(self):
        """Approve BOM when percentage = 100% and component KG matches Total Qty (Kgs)."""
        for bom in self:
            if not bom.bom_line_ids:
                raise ValidationError(_('Cannot approve: add at least one component.'))

            pct_total = sum(bom.bom_line_ids.mapped('percentage'))
            if float_compare(pct_total, 1.0, precision_digits=5) != 0:
                raise ValidationError(_(
                    'Cannot approve: total percentage must be 100%% '
                    '(currently %.2f%%).'
                ) % (pct_total * 100.0))

            total_kgs = bom.product_qty or 0.0
            component_kg = bom.total_component_qty_kg or 0.0
            if float_compare(component_kg, total_kgs, precision_digits=5) != 0:
                raise ValidationError(_(
                    'Cannot approve: Total Components (KG) (%.4f) must match '
                    'Total Qty (Kgs) (%.4f).'
                ) % (component_kg, total_kgs))

            bom.write({
                'state': 'approved',
                'batch_approval_time': fields.Datetime.now(),
            })
        return True


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    percentage = fields.Float(
        string='Percentage',
        digits=(16, 5),
        help='Enter as fraction, e.g. 0.435 for 43.5%. '
             'Qty in KG = Total Qty (Kgs) × Percentage. Total of all lines ≤ 100%.',
    )
    density = fields.Float(
        string='Density',
        digits=(16, 4),
        help='Qty in Ltr = Qty in KG (product_qty) / Density.',
    )
    qty_ltr = fields.Float(
        string='Qty in Ltr',
        compute='_compute_qty_ltr',
        store=True,
        digits='Product Unit',
        help='Qty in Ltr = product_qty / Density.',
    )
    actual_qty_ltr = fields.Float(string='Actual Qty Ltr', digits='Product Unit')
    actual_qty_kg = fields.Float(string='Actual Qty KG', digits='Product Unit')

    @api.depends('product_qty', 'density')
    def _compute_qty_ltr(self):
        """Qty in Ltr = product_qty / Density."""
        for line in self:
            dens = line.density or 0.0
            line.qty_ltr = (line.product_qty / dens) if dens else 0.0

    @api.onchange('percentage')
    def _onchange_percentage(self):
        """Qty in KG = BOM Total Qty (Kgs) × Percentage."""
        if self.percentage:
            self.product_qty = (self.bom_id.product_qty or 0.0) * self.percentage

    @api.constrains('percentage')
    def _check_percentage_total(self):
        for bom in self.mapped('bom_id'):
            total = sum(bom.bom_line_ids.mapped('percentage'))
            if float_compare(total, 1.0, precision_digits=5) > 0:
                raise ValidationError(_(
                    'Total component percentage cannot exceed 100%% '
                    '(currently %.2f%%).'
                ) % (total * 100.0))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            percentage = vals.get('percentage')
            if percentage:
                bom = self.env['mrp.bom'].browse(vals.get('bom_id'))
                vals['product_qty'] = (bom.product_qty or 0.0) * percentage
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_blend_sync'):
            return res
        if 'percentage' in vals:
            for line in self.filtered('percentage'):
                qty_kg = (line.bom_id.product_qty or 0.0) * line.percentage
                super(MrpBomLine, line).write({'product_qty': qty_kg})
        return res
