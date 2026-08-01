# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConclusionPoint(models.Model):
    _name = 'conclusion.point'
    _description = 'Conclusion Point'

    name = fields.Char(string="Conclusion Point", required=True)
    event_id = fields.Many2one('calendar.event', string="Event")


class HelpdeskSnapshotLine(models.Model):
    _name = 'helpdesk.snapshot.line'
    _description = 'Complain Snapshot Line'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('ticket_id', '=', vals.get('ticket_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class HelpdeskNatureLine(models.Model):
    _name = 'helpdesk.nature.line'
    _description = 'Nature of Complain Line'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('ticket_id', '=', vals.get('ticket_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class HelpdeskReviewLine(models.Model):
    _name = 'helpdesk.review.line'
    _description = 'Petrogulf Review Line'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('ticket_id', '=', vals.get('ticket_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class HelpdeskSolutionLine(models.Model):
    _name = 'helpdesk.solution.line'
    _description = 'Petrogulf Proposed Solution Line'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('ticket_id', '=', vals.get('ticket_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class HelpdeskLearningLine(models.Model):
    _name = 'helpdesk.learning.line'
    _description = 'Learning from Case Line'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('ticket_id', '=', vals.get('ticket_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class Amendment(models.Model):
    _name = 'amendment.amendment'
    _description = 'Amendment Remark'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    remarks = fields.Text(string="Remarks")
    amendment_reason_id = fields.Many2one("sale.reason", string="Amendment Reason")
    amendment_date = fields.Date(string="Amendment Date")
    user_id = fields.Many2one("res.users", string="User")
    sale_id = fields.Many2one('sale.order', string="Sale Order")

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('sale_id', '=', vals.get('sale_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1
        return super().create(vals)


class LoadedBy(models.Model):
    _name = 'loaded.by'
    _description = 'Loaded by'

    name = fields.Char(string="Loaded by", required=True)
