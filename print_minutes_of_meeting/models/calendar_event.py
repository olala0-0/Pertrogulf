# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)

#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
import logging
import pytz
from odoo.tools import format_datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    """Extend mail.template to add reminder configuration fields"""
    _inherit = 'mail.template'

    is_reminder = fields.Boolean(string='Is Reminder Template', default=False, help='Check if this template should be used for reminders')
    reminder_before = fields.Float(string='Send Before', help='Time value before the event/deadline to send the reminder')
    reminder_unit = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days')
    ], string='Time Unit', default='minutes', help='Unit of time for the reminder')

    def get_delta(self):
        """Convert the reminder time value and unit to a timedelta"""
        self.ensure_one()
        value = int(self.reminder_before)  # Convert float to int
        if self.reminder_unit == 'minutes':
            return timedelta(minutes=value)
        elif self.reminder_unit == 'hours':
            return timedelta(hours=value)
        elif self.reminder_unit == 'days':
            return timedelta(days=value)
        return timedelta()


class CalendarEvent(models.Model):
    """Inheriting fields for in calendar event to get the details """
    _inherit = 'calendar.event'

    responsible_user_id = fields.Many2one('res.users',
                                          help="The person who is responsible "
                                               "for the event",
                                          string='Responsible User')
    note_taker_id = fields.Many2one('res.partner',
                                    domain="[('id', 'in', partner_ids)]",
                                    help="The note taker", string='Note Taker')
    absent_member_ids = fields.Many2many('res.partner',
                                         'res_partner_absent_member_rel',
                                         domain="[('id', 'in', partner_ids)]",
                                         help="Absent members of the meeting",
                                         string='Absent Member')
    agenda_ids = fields.One2many('meeting.agenda', 'calendar_event_id',
                                 string='Agenda', help='The meeting agendas', copy=True)
    actions_ids = fields.One2many('meeting.actions', 'calendar_event_id',
                                  string='Actions/Decisions',
                                  help='The meeting actions or decisions', copy=True)
    notes = fields.Html(string='Conclusions', help='Meeting conclusions')
    is_user = fields.Boolean(compute='_compute_is_user', string='Is User',
                             help='Is user or not')
    meeting_reminder_sent = fields.Boolean(string='Meeting Reminder Sent', default=False)


    def get_local_datetime(self, datetime_field):
        """Convert datetime to user's timezone and add 1.5 hours"""
        if not datetime_field:
            return False
        # Get timezone - prioritize user timezone over context
        tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        # Convert to user timezone
        user_tz = pytz.timezone(tz_name)
        local_dt = datetime_field.astimezone(user_tz)
        # Add 1.5 hours (1 hour 30 minutes) to the converted datetime
        final_dt = local_dt + timedelta(hours=1, minutes=30)
        return final_dt.strftime('%d/%b/%Y %H:%M:%S %A')

    @api.model
    def _send_meeting_reminder_email(self):
        """Cron job to send meeting reminder emails"""
        reminder_templates = self.env['mail.template'].search([
            ('is_reminder', '=', True),
            ('model_id.model', '=', 'calendar.event')
        ])
        
        now = fields.Datetime.now()
        
        for template in reminder_templates:
            delta = template.get_delta()
            
            # Find meetings that haven't had their reminder sent and are coming up
            events = self.search([
                ('meeting_reminder_sent', '=', False),
                ('start', '>', now), 
                ('start', '<=', now + delta)
            ])
            
            for event in events:
                template.send_mail(event.id, force_send=True)
                event.meeting_reminder_sent = True
                _logger.info(f"Meeting reminder sent for event {event.id}")

    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     real_events = super().search_read(domain, fields, offset=offset, limit=limit, order=order)

    #     today = date.today()
    #     year = today.year
    #     virtual_events = []

    #     partners = self.env['res.partner'].search([
    #         '|', ('date_of_birth', '!=', False), ('date_of_anniversary', '!=', False)
    #     ])

    #     for partner in partners:
    #         # Birthday
    #         if partner.date_of_birth:
    #             try:
    #                 bday = partner.date_of_birth.replace(year=year)
    #             except ValueError:
    #                 bday = partner.date_of_birth.replace(year=year, day=28)  # handle Feb 29
    #             start_dt = datetime.combine(bday, datetime.min.time())
    #             stop_dt = start_dt + timedelta(hours=1)

    #             virtual_events.append({
    #                 'id': -partner.id,
    #                 'name': f"{partner.name}'s Birthday 🎂",
    #                 'start': start_dt.isoformat(),
    #                 'stop': stop_dt.isoformat(),
    #                 'allday': True,
    #                 'partner_ids': [partner.id],
    #                 'is_virtual': True,
    #             })

    #         # Anniversary
    #         if partner.date_of_anniversary:
    #             try:
    #                 anniv = partner.date_of_anniversary.replace(year=year)
    #             except ValueError:
    #                 anniv = partner.date_of_anniversary.replace(year=year, day=28)
    #             start_dt = datetime.combine(anniv, datetime.min.time())
    #             stop_dt = start_dt + timedelta(hours=1)

    #             virtual_events.append({
    #                 'id': -(100000 + partner.id),
    #                 'name': f"{partner.name}'s Anniversary 💍",
    #                 'start': start_dt.isoformat(),
    #                 'stop': stop_dt.isoformat(),
    #                 'allday': True,
    #                 'partner_ids': [partner.id],
    #                 'is_virtual': True,
    #             })

    #     return real_events + virtual_events

    @api.depends('responsible_user_id')
    def _compute_is_user(self):
        """Function to set is the responsible user is same as the login user"""
        for rec in self:
            rec.is_user = bool(rec.responsible_user_id.id == self.env.user.id)

    def action_send_mail(self):
        """Function for send mail to the recipients"""
        report_template_id = self.env['ir.actions.report']._render_qweb_pdf(
            report_ref='print_minutes_of_meeting.action_minutes_of_meeting_report',
            data=None,
            res_ids=self.ids,
        )
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Minutes of Meeting",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        template_id = self.env.ref(
            'print_minutes_of_meeting.email_template_minutes_of_meeting')
        template_id.attachment_ids = [(6, 0, [data_id.id])]
        context = {
            'name': self.name,
        }
        email_values = {
            'recipient_ids': [(4, partner) for partner in
                              self.partner_ids.ids],
            'email_from': self.responsible_user_id.email
        }
        self.env['mail.template'].browse(template_id.id).with_context(
            context=context).send_mail(self.id, email_values=email_values,
                                       force_send=True)
        template_id.attachment_ids = [(3, data_id.id)]

    def _send_assigned_tasks_email(self):
        """Send emails to assigned partners about their tasks after meeting creation"""
        for event in self:
            if not event.actions_ids:
                continue
                
            # Group tasks by assigned partner
            tasks_by_partner = {}
            for action in event.actions_ids:
                for partner in action.assigned_partner_ids:
                    if partner.id not in tasks_by_partner:
                        tasks_by_partner[partner.id] = []
                    tasks_by_partner[partner.id].append(action)
            
            # Send email to each partner
            template_id = self.env.ref('print_minutes_of_meeting.email_template_assigned_tasks')
            for partner_id, actions in tasks_by_partner.items():
                partner = self.env['res.partner'].browse(partner_id)
                template_id.with_context(partner=partner, actions=actions).send_mail(event.id, force_send=True)
                _logger.info(f"Assigned tasks email sent to partner {partner_id} for event {event.id}")
    
    @api.model
    def create(self, vals):
        """Override create to send emails after meeting creation"""
        event = super(CalendarEvent, self).create(vals)
        if event.actions_ids:
            event._send_assigned_tasks_email()
        return event
    
    def write(self, vals):
        """Override write to send emails when actions are updated"""
        result = super(CalendarEvent, self).write(vals)
        if 'actions_ids' in vals:
            for event in self:
                event._send_assigned_tasks_email()
        return result


class MeetingAgenda(models.Model):
    """Class for adding meeting agenda"""
    _name = 'meeting.agenda'
    _description = 'Meeting Agenda'
    _rec_name = 'topic'

    topic = fields.Char(string='Topic', help='Agenda Topic')
    description = fields.Text(string='Description',
                              help='Description of the Meeting')
    is_discussed = fields.Boolean(string='Discussed',
                                  help='The topic is discussed or not')
    calendar_event_id = fields.Many2one('calendar.event', string='Event',
                                        help='The Calender Event')


class MeetingActions(models.Model):
    """Class for adding meeting actions"""
    _name = 'meeting.actions'
    _description = 'Meeting Actions'

    def _responsible_partner_id_domain(self):
        """Return the domain for responsible partner"""
        return [('id', 'in', self.calendar_event_id.partner_ids.ids)]

    action = fields.Char(string='Action', help='The action took on the meeting')
    reminder_sent = fields.Boolean(string='Deadline Reminder Sent', default=False)
    description = fields.Text(string='Description',
                              help='The action description')
    agenda_item_id = fields.Many2one('meeting.agenda', string='Agenda',
                                     help='The agenda item')
    responsible_partner_id = fields.Many2one('res.partner',
                                             string='Responsible Partner',
                                             help='The Responsible person for the action',
    )
    assigned_partner_ids = fields.Many2many('res.partner',
                                            string='Assigned Partners',
                                            help='The assigned partners of the action'
                                            )
    calendar_event_id = fields.Many2one('calendar.event', string='Event',
                                        help='Related event of the action')
    deadline = fields.Date(string='Deadline', help='Deadline for the action')
    previous_meeting_id = fields.Many2one('calendar.event', string="Previous Meeting")
    previous_meeting_date = fields.Date(string="Previous Meeting Date", related="previous_meeting_id.start_date")
    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('wip', 'Work In Progress'),
        ('completed', 'Completed')
    ], string="Status", default="not_started")
    remarks = fields.Text(string="Remarks")
    attachment_id = fields.Many2one('ir.attachment', string="Attach File")
    attachment_name = fields.Char(string="Filename")
    attachment_data = fields.Binary(string="Attach File", attachment=True)
    extension_1 = fields.Date(string="Extension 1")
    extension_2 = fields.Date(string="Extension 2")
    extension_3 = fields.Date(string="Extension 3")
    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('calendar_event_id', '=', vals.get('calendar_event_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)

    @api.onchange('calendar_event_id')
    def _onchange_calendar_event_id(self):
        for rec in self:
            rec.previous_meeting_id = False
            if rec.calendar_event_id and rec.calendar_event_id.start:
                previous = self.env['calendar.event'].search([
                    ('start', '<', rec.calendar_event_id.start),
                    ('id', '!=', rec.calendar_event_id.id)
                ], order='start desc', limit=1)

                if previous:
                    rec.previous_meeting_id = previous.id

    @api.model
    def _send_deadline_reminder_email(self):
        """Cron job to send task deadline reminder emails"""
        reminder_templates = self.env['mail.template'].search([
            ('is_reminder', '=', True),
            ('model_id.model', '=', 'meeting.actions')
        ])
        now = fields.Date.context_today(self)
        for template in reminder_templates:
            delta = template.get_delta()
            # Find actions with approaching deadlines
            actions = self.search([
                ('reminder_sent', '=', False),
                ('status', '!=', 'completed'),
                ('deadline', '!=', False),
                ('deadline', '>=', now),
                ('deadline', '<=', fields.Date.to_string(fields.Date.from_string(now) + delta))
            ])
            for action in actions:
                template.send_mail(action.id, force_send=True)
                action.reminder_sent = True
                _logger.info(f"Deadline reminder sent for action {action.id}")

    def write(self, vals):
        """Override write to send emails when status changes"""
        old_statuses = {record.id: record.status for record in self}
        result = super(MeetingActions, self).write(vals)
        if 'status' in vals:
            for action in self:
                if action.status != old_statuses[action.id]:
                    template_id = self.env.ref('print_minutes_of_meeting.email_template_status_change')
                    # Send to meeting organizer
                    if action.calendar_event_id and action.calendar_event_id.user_id:
                        template_id.with_context(old_status=old_statuses[action.id]).send_mail(action.id, force_send=True)
                    # Send to current user if different from organizer
                    current_user = self.env.user
                    if current_user != action.calendar_event_id.user_id:
                        template_id.with_context(old_status=old_statuses[action.id]).send_mail(
                            action.id, 
                            force_send=True, 
                            email_values={'email_to': current_user.partner_id.email}
                        )
        return result
