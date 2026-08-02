# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleContainerAllocation(models.Model):
    _name = 'sale.container.allocation'
    _description = 'Sale Container Allocation'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True, ondelete='cascade')
    container_id = fields.Many2one('container.master', string="Container", required=True)
    quantity = fields.Integer(string="Quantity", required=True)
    total_capacity = fields.Float(string="Total Capacity (kg)", compute="_compute_total_capacity", store=True)

    @api.depends('container_id', 'quantity')
    def _compute_total_capacity(self):
        for record in self:
            record.total_capacity = record.container_id.weight_capacity * record.quantity


class AdnocStage(models.Model):
    _name = 'adnoc.stage'
    _description = 'Adnoc Stage'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    process_stage_id = fields.Many2one('process.stage', string="Process Stage")
    stage = fields.Char(string="Stage")
    user_id = fields.Many2one('res.users', string="User")
    create_date = fields.Datetime(string="Create Date", readonly=True, default=fields.Datetime.now)
    remarks = fields.Text(string="Remarks")
    next_action_date = fields.Datetime(string="Next Action Date")
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    progress = fields.Char(string="Progress")
    # business_unit = fields.Selection([
    #     ('automotive', 'Automotive Industrial'),
    #     ('adnoc', 'ADNOC'),
    # ], string="Business Unit")
    # team_id = fields.Many2one("process.master", string="Team")
    team_id = fields.Many2one("process.user.master", string="Team")
    business_unit = fields.Selection(related="team_id.business_unit", string="Business Unit", store=True)
    user_ids_allowed = fields.Many2many('res.users', compute='_compute_user_ids_allowed', store=False)

    @api.depends('team_id')
    def _compute_user_ids_allowed(self):
        for record in self:
            if record.team_id:
                record.user_ids_allowed = record.team_id.user_ids.ids if record.team_id.user_ids else []
            else:
                record.user_ids_allowed = self.env['res.users']

    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     if self.user_id:
    #         teams = self.env['process.user.master'].search([('user_ids', 'in', self.user_id.id)])
    #         return {'domain': {'team_id': [('id', 'in', teams.ids)]}}
    #     return {}

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            process_master = self.team_id.team_id  # `team_id` in process.user.master is Many2one to process.master
            self.stage = process_master.stage or ''
            self.progress = process_master.progress or ''
            self.business_unit = process_master.business_unit or ''
        #     user_masters = self.env['process.user.master'].search([('team_id', '=', self.team_id.id)])
        #     user_ids = []
        #     for user_master in user_masters:
        #         user_ids.extend(user_master.user_ids.ids)
        #     if user_ids:
        #         return {'domain': {'user_id': [('id', 'in', user_ids)]}}
        # return {'domain': {'user_id': [('id', '=', False)]}}

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('sale_id', '=', vals.get('sale_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1

        # Automatically set create_date if not already set
        if not vals.get('create_date'):
            vals['create_date'] = fields.Datetime.now()

        # Set user_id to current user if not provided
        # if not vals.get('user_id'):
        #     vals['user_id'] = self.env.uid
        return super().create(vals)


class AutomotiveStage(models.Model):
    _name = 'automotive.stage'
    _description = 'Automotive Stage'

    sequence = fields.Integer(string="Sr. No", readonly=True, default=0)
    process_stage_id = fields.Many2one('process.stage', string="Process Stage")
    stage = fields.Char(string="Stage")
    user_id = fields.Many2one('res.users', string="User")
    create_date = fields.Datetime(string="Create Date", readonly=True, default=fields.Datetime.now)
    remarks = fields.Text(string="Remarks")
    next_action_date = fields.Datetime(string="Next Action Date")
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    progress = fields.Char(string="Progress")
    business_unit = fields.Selection([
        ('automotive', 'Automotive Industrial'),
        ('adnoc', 'ADNOC'),
    ], string="Business Unit")
    # team_id = fields.Many2one("process.master", string="Team")
    team_id = fields.Many2one("process.user.master", string="Team")
    business_unit = fields.Selection(related="team_id.business_unit", string="Business Unit", store=True)
    user_ids_allowed = fields.Many2many('res.users', compute='_compute_user_ids_allowed', store=False)

    @api.depends('team_id')
    def _compute_user_ids_allowed(self):
        for record in self:
            if record.team_id:
                record.user_ids_allowed = record.team_id.user_ids.ids if record.team_id.user_ids else []
            else:
                record.user_ids_allowed = self.env['res.users']

    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     if self.user_id:
    #         teams = self.env['process.user.master'].search([('user_ids', 'in', self.user_id.id)])
    #         return {'domain': {'team_id': [('id', 'in', teams.ids)]}}
    #     return {}

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            process_master = self.team_id.team_id  # `team_id` in process.user.master is Many2one to process.master
            self.stage = process_master.stage or ''
            self.progress = process_master.progress or ''
            self.business_unit = process_master.business_unit or ''
        #     user_masters = self.env['process.user.master'].search([('team_id', '=', self.team_id.id)])
        #     user_ids = []
        #     for user_master in user_masters:
        #         user_ids.extend(user_master.user_ids.ids)
        #     if user_ids:
        #         return {'domain': {'user_id': [('id', 'in', user_ids)]}}
        # return {'domain': {'user_id': [('id', '=', False)]}}

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            max_seq = self.search([('sale_id', '=', vals.get('sale_id'))], order="sequence desc", limit=1).sequence or 0
            vals['sequence'] = max_seq + 1

        # Automatically set create_date if not already set
        if not vals.get('create_date'):
            vals['create_date'] = fields.Datetime.now()

        # Set user_id to current user if not provided
        # if not vals.get('user_id'):
        #     vals['user_id'] = self.env.uid
        return super().create(vals)
