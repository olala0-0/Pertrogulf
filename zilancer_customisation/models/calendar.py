from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    conclusion_point_ids = fields.One2many(
        'conclusion.point', 'event_id', string="Conclusion Points"
    )
    meeting_id = fields.Char(string="Meeting ID", readonly=True, copy=False, default="New")
    business_unit = fields.Selection([
        ('pg_marine', 'PG-Marine'),
        ('pg_auto', 'PG-Auto'),
        ('pg_powerx', 'PG-PowerX'),
        ('pg_aviation', 'PG-Aviation'),
        ('pg_tblnd', 'PG-Toll Blending')
    ], string="Business Unit", required=True)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('meeting_id', 'New') == 'New':
    #             vals['meeting_id'] = self.env['ir.sequence'].next_by_code('calendar.event') or 'New'
    #     return super(CalendarEvent, self).create(vals)

    @api.model
    def create(self, vals):
        if vals.get('meeting_id', 'New') == 'New' and vals.get('business_unit'):
            bu = vals.get('business_unit')
            if not bu:
                raise UserError("Business Unit is required to generate the sequence.")
            bu_prefix = {
                'pg_marine': 'PG-MARINE',
                'pg_auto': 'PG-AUTO',
                'pg_powerx': 'PG-POWERX',
                'pg_aviation': 'PG-AVIATION',
                'pg_tblnd': 'PG-TBLND',
            }.get(vals['business_unit'], 'PG')

            now = fields.Date.today()
            date_code = now.strftime('%b').upper() + now.strftime('%y')  # APR25

            # Count existing meetings for this business unit in this month/year
            existing_count = self.search_count([
                ('business_unit', '=', vals['business_unit']),
                ('create_date', '>=', now.replace(day=1)),
                ('create_date', '<=', now),
            ])

            seq_number = str(existing_count + 1).zfill(6)

            vals['meeting_id'] = f"{bu_prefix}-{date_code}-{seq_number}"

        return super().create(vals)


class MeetingActions(models.Model):
    """Class for adding meeting actions"""
    _inherit = 'meeting.actions'

    meeting_id = fields.Char(related="calendar_event_id.meeting_id", string="Meeting ID", store=True)
    meeting_date = fields.Datetime(related="calendar_event_id.start", string="Meeting Date", store=True)
