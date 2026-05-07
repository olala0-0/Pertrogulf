from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime



class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    planned_closure_date = fields.Date(string="Planned Closure Date")
    packaging_material_available = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Packaging Material Available", default='no')
    expected_arrival_date = fields.Date(string="Expected Arrival Date")
    parent_ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Parent Ticket", ondelete="restrict"
    )
    child_ticket_ids = fields.One2many(
        "helpdesk.ticket", "parent_ticket_id", string="Child Tickets"
    )
    # helpdesk.ticket.stage
    # state = fields.Selection(selection_add=[('closed', 'Closed')])
    original_complain_date = fields.Date(string="Original Complain Date")
    snapshot_line_ids = fields.One2many('helpdesk.snapshot.line', 'ticket_id', string="Complain Snapshot")
    nature_line_ids = fields.One2many('helpdesk.nature.line', 'ticket_id', string="Nature of Complain")
    review_line_ids = fields.One2many('helpdesk.review.line', 'ticket_id', string="Petrogulf Review")
    solution_line_ids = fields.One2many('helpdesk.solution.line', 'ticket_id', string="Proposed Solution")
    learning_line_ids = fields.One2many('helpdesk.learning.line', 'ticket_id', string="Learning from Case")
    business_unit = fields.Selection([
        ('pg_marine', 'PG-Marine'),
        ('pg_auto', 'PG-Auto'),
        ('pg_powerx', 'PG-PowerX'),
        ('pg_aviation', 'PG-Aviation'),
        ('pg_tblnd', 'PG-Toll Blending')
    ], string="Business Unit", required=True)
    # name = fields.Char(string='Subject', readonly=True, copy=False, default="New")
    number = fields.Char(string="Ticket number", readonly=True, copy=False, default="New")

    @api.model
    def create(self, vals):
        # Get the current month abbreviation and year
        if vals.get('number', _('New')) == _('New'):
            bu = vals.get('business_unit')
            if not bu:
                raise UserError("Business Unit is required to generate the sequence.")

            # Get prefix by business unit
            prefix_map = {
                'pg_marine': 'PG-MARINE',
                'pg_auto': 'PG-AUTO',
                'pg_powerx': 'PG-POWERX',
                'pg_aviation': 'PG-AVIATION',
                'pg_tblnd': 'PG-TBLND',
            }
            prefix = prefix_map.get(bu, 'PG')

            # Month & Year
            now = datetime.now()
            month = now.strftime('%b').upper()   # APR
            year = now.strftime('%Y')            # 2025

            # Build full prefix
            full_prefix = f"{prefix}-HT-{month}-{year}-"

            # Find existing inquiries with same prefix to count
            last = self.search([('number', 'ilike', full_prefix)], order='id desc', limit=1)
            if last and last.number:
                last_number = int(last.number.split('-')[-1])
                number = last_number + 1
            else:
                number = 1

            vals['number'] = f"{full_prefix}{str(number).zfill(7)}"

        return super(HelpdeskTicket, self).create(vals)
    @api.constrains("stage_id")
    def _check_child_tickets_closed(self):
        for ticket in self:
            if ticket.stage_id.name == "Closed" and ticket.child_ticket_ids.filtered(lambda t: t.stage_id.name != "Closed"):
                raise ValidationError("You cannot close a Parent Ticket until all Child Tickets are closed.")

    # @api.model
    def _check_required_tabs(self):
        for record in self:
            if record.stage_id.name == "Completed":
                if not record.snapshot_line_ids:
                    raise ValidationError(_("Please add at least one line in 'Complain Snapshot'."))
                if not record.nature_line_ids:
                    raise ValidationError(_("Please add at least one line in 'Nature of Complain'."))
                if not record.review_line_ids:
                    raise ValidationError(_("Please add at least one line in 'Petrogulf Review'."))
                if not record.solution_line_ids:
                    raise ValidationError(_("Please add at least one line in 'Proposed Solution'."))
                if not record.learning_line_ids:
                    raise ValidationError(_("Please add at least one line in 'Learning from this Case'."))

    def write(self, vals):
        res = super(HelpdeskTicket, self).write(vals)
        if 'stage_id' in vals:
            self._check_required_tabs()
        return res

