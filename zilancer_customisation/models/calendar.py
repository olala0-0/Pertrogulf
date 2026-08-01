from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.sale_order_enquiry.business_unit_data import (
    BUSINESS_UNIT_SELECTION,
    get_business_unit_prefix,
)
from datetime import datetime


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    conclusion_point_ids = fields.One2many(
        'conclusion.point', 'event_id', string="Conclusion Points"
    )
    meeting_id = fields.Char(string="Meeting ID", readonly=True, copy=False, default="New")
    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('meeting_id', 'New') == 'New' and vals.get('business_unit'):
                bu = vals.get('business_unit')
                if not bu:
                    raise UserError("Business Unit is required to generate the sequence.")
                bu_prefix = get_business_unit_prefix(vals['business_unit']) or 'PG'

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

        return super().create(vals_list)


class MeetingActions(models.Model):
    """Class for adding meeting actions"""
    _inherit = 'meeting.actions'

    meeting_id = fields.Char(related="calendar_event_id.meeting_id", string="Meeting ID", store=True)
    meeting_date = fields.Datetime(related="calendar_event_id.start", string="Meeting Date", store=True)
