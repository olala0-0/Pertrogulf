from odoo import fields, models, api
from datetime import timedelta
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vessel_no = fields.Char(string="Vessel No", required=False)
    invoice_no = fields.Char(string="Invoice No", required=False)
    invoice_date = fields.Date(string="Invoice Date", required=False)
    expected_arrival_days = fields.Selection([
        ('30', '30'),
        ('60', '60'),
        ('90', '90'),
        ('120', '120'),
        ('others', 'Others')
    ], string="Expected Arrival Days")
    other_expected_days = fields.Integer(string="Other Days")
    eta_date = fields.Date(string="ETA Date", compute="_compute_eta_date", store=True)
    eta1 = fields.Date("ETA 1")
    remark1 = fields.Text("Remark 1")
    eta2 = fields.Date("ETA 2")
    remark2 = fields.Text("Remark 2")
    eta3 = fields.Date("ETA 3")
    remark3 = fields.Text("Remark 3")
    actual = fields.Date("Actual Arrival Date")
    final_remark = fields.Text("Final Remark")
    custom_no = fields.Char(string="Custom No")

    # PG TOLL FIELDS
    document_type = fields.Selection([
        ('general_dispatch', 'General Dispatch Note'),
        ('dispatch_advise', 'Dispatch Advise / Gatepass')
    ], string='Document Type')
    # widget='radio'

    document_number = fields.Char(string='Document Number', copy=False, readonly=True)

    # Additional fields
    customer_lpo_no = fields.Char(string='Customer LPO No')
    container_no = fields.Char(string='Container No')
    seal_no = fields.Char(string='Seal No')
    vehicle_no = fields.Char(string='Vehicle No')

    # Driver Details tab fields
    driver_name = fields.Char(string='Driver Name')
    driver_id = fields.Char(string='Driver ID')
    driver_emirates_id = fields.Binary(string='Driver Emirates ID', attachment=True)
    driver_emirates_id_filename = fields.Char(string='ID File Name')

    # Document Details tab fields
    prepared_by = fields.Char(string='Prepared By')
    loaded_by = fields.Char(string='Loaded By')
    loaded_by_id = fields.Many2one('loaded.by', string='Loaded By')
    approved_by = fields.Char(string='Approved By')
    receiver_name = fields.Char(string='Receiver Name')
    receiver_sign = fields.Char(string='Receiver Sign (Print Only)')

    @api.model_create_multi
    def create(self, vals_list):
        # Handle structural conversion for multi-record creation loops in modern Odoo
        for vals in vals_list:
            # Generate document number only if document_type is set
            if vals.get('document_type') and not vals.get('document_number'):
                vals['document_number'] = self._generate_document_number_simple(vals['document_type'])
        return super(StockPicking, self).create(vals_list)
    
    def write(self, vals):
        # If document_type is changed and picking is not done/draft, regenerate document number
        if 'document_type' in vals and vals['document_type'] != self.document_type:
            # Only regenerate if the type actually changed
            for picking in self:
                if picking.state in ['draft', 'assigned']:  # Only allow regeneration in draft/assigned states
                    if vals['document_type']:
                        vals['document_number'] = self._generate_document_number_simple(vals['document_type'])
        return super(StockPicking, self).write(vals)
    
    @api.onchange('document_type')
    def _onchange_document_type(self):
        """Generate document number on change of document type - only in draft state"""
        if self.document_type and not self.document_number and self.state in ['draft', False]:
            self.document_number = self._generate_document_number_simple(self.document_type)
        elif self.document_type and self.document_number and self.state in ['draft', False]:
            # If document type changed and we're in draft state, regenerate number
            # Check if the prefix matches the current document type
            current_prefix = self._get_prefix_from_document_type(self.document_type)
            if current_prefix and not self.document_number.startswith(current_prefix):
                self.document_number = self._generate_document_number_simple(self.document_type)
    
    def _get_prefix_from_document_type(self, doc_type):
        """Get prefix based on document type"""
        if doc_type == 'general_dispatch':
            return 'PG-GDN'
        elif doc_type == 'dispatch_advise':
            return 'PG-DAG'
        return None
    
    def _generate_document_number_simple(self, document_type):
        """Simple document number generation that resets sequence based on document type"""
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        if document_type == 'general_dispatch':
            prefix = 'PG-GDN'
        else:
            prefix = 'PG-DAG'
        
        # Find the highest existing number for today AND this specific document type
        existing = self.search([
            ('document_type', '=', document_type),
            ('document_number', 'like', f'{prefix}-{date_str}-%')
        ], order='document_number desc', limit=1)
        
        if existing and existing.document_number:
            try:
                # Extract the sequence number from the document number
                last_num = int(existing.document_number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}-{date_str}-{next_num:05d}"
    
    def action_regenerate_document_number(self):
        """Manual action to regenerate document number"""
        for picking in self:
            if picking.document_type and picking.state in ['draft', 'assigned']:
                picking.document_number = picking._generate_document_number_simple(picking.document_type)
        return True

    @api.depends('scheduled_date', 'expected_arrival_days', 'other_expected_days')
    def _compute_eta_date(self):
        for rec in self:
            days = int(rec.expected_arrival_days) if rec.expected_arrival_days and rec.expected_arrival_days != 'others' else rec.other_expected_days or 0
            rec.eta_date = rec.scheduled_date + timedelta(days=days) if rec.scheduled_date else False


class StockMove(models.Model):
    _inherit = 'stock.move'

    package = fields.Char("Package")
    pack = fields.Char("Pack")
    remarks = fields.Text("Dispatch Instructions")
    batch_no = fields.Char("Batch No")
    mfg_date = fields.Date("Mfg Dt")
    sap_fg_code = fields.Char(
        related="product_id.sap_fg_code",
        string="SAP FG code", store=True)
    sample_type = fields.Char("Sample Type", default="Kettle + Filling Sample")
    exp_date = fields.Date("Exp Dt")

    def _assign_picking_post_process(self, new=False):
        """Copy SO delivery special instructions onto the delivery note."""
        res = super()._assign_picking_post_process(new=new)
        if not new:
            return res
        for picking in self.mapped('picking_id'):
            sale = picking.sale_id
            if (
                sale
                and sale.delivery_special_instructions
                and not picking.note
            ):
                picking.note = sale.delivery_special_instructions
        return res


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields.append('remarks')
        return fields
