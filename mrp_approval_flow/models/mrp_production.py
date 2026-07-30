# -*- coding: utf-8 -*-
"""
Manufacturing Order approval: QC first, then Store In-ward,
before Confirm / start of the MO.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mo_approval_state = fields.Selection(
        [
            ('pending_qc', 'QC'),
            ('pending_store', 'Store'),
            ('approved', 'Approved'),
        ],
        string='MO Approval',
        default='pending_qc',
        copy=False,
        tracking=True,
        help='QC must approve first, then Store In-ward, before Confirm.',
    )
    # Single statusbar: QC → Store → Approved → Confirmed → Done
    mo_display_stage = fields.Selection(
        [
            ('pending_qc', 'QC'),
            ('pending_store', 'Store'),
            ('approved', 'Approved'),
            ('confirmed', 'Confirmed'),
            ('progress', 'In Progress'),
            ('to_close', 'To Close'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        compute='_compute_mo_display_stage',
        store=True,
    )
    qc_approved_by = fields.Many2one(
        'res.users',
        string='QC Approved By',
        copy=False,
        readonly=True,
        tracking=True,
    )
    qc_approved_date = fields.Datetime(
        string='QC Approval Date',
        copy=False,
        readonly=True,
    )
    store_approved_by = fields.Many2one(
        'res.users',
        string='Store Approved By',
        copy=False,
        readonly=True,
        tracking=True,
    )
    store_approved_date = fields.Datetime(
        string='Store Approval Date',
        copy=False,
        readonly=True,
    )

    @api.depends('state', 'mo_approval_state')
    def _compute_mo_display_stage(self):
        for production in self:
            if production.state == 'cancel':
                production.mo_display_stage = 'cancel'
            elif production.state == 'done':
                production.mo_display_stage = 'done'
            elif production.state in ('confirmed', 'progress', 'to_close'):
                production.mo_display_stage = production.state
            elif production.mo_approval_state == 'pending_store':
                production.mo_display_stage = 'pending_store'
            elif production.mo_approval_state == 'approved':
                production.mo_display_stage = 'approved'
            else:
                production.mo_display_stage = 'pending_qc'

    def _mrp_approval_reset_vals(self):
        return {
            'mo_approval_state': 'pending_qc',
            'qc_approved_by': False,
            'qc_approved_date': False,
            'store_approved_by': False,
            'store_approved_date': False,
        }

    def action_confirm(self):
        for production in self:
            if production.mo_approval_state != 'approved':
                if production.mo_approval_state == 'pending_qc':
                    raise UserError(_(
                        'Cannot confirm Manufacturing Order %(mo)s.\n'
                        'Waiting for QC Approval first.'
                    ) % {'mo': production.name})
                if production.mo_approval_state == 'pending_store':
                    raise UserError(_(
                        'Cannot confirm Manufacturing Order %(mo)s.\n'
                        'QC is approved; waiting for Store In-ward Approval.'
                    ) % {'mo': production.name})
                raise UserError(_(
                    'Cannot confirm Manufacturing Order %(mo)s until QC and Store approvals are done.'
                ) % {'mo': production.name})
        return super().action_confirm()

    def action_cancel(self):
        res = super().action_cancel()
        self.write(self._mrp_approval_reset_vals())
        return res

    def action_qc_approval(self):
        """Step 1 — QC Approval (before Confirm)."""
        for production in self:
            if production.state != 'draft':
                raise UserError(_(
                    'QC Approval is only allowed on draft Manufacturing Order %(mo)s.'
                ) % {'mo': production.name})
            if production.mo_approval_state != 'pending_qc':
                raise UserError(_(
                    'Manufacturing Order %(mo)s is not waiting for QC approval.\n'
                    'Current status: %(status)s'
                ) % {
                    'mo': production.name,
                    'status': dict(production._fields['mo_approval_state'].selection).get(
                        production.mo_approval_state, production.mo_approval_state
                    ),
                })
            production.write({
                'mo_approval_state': 'pending_store',
                'qc_approved_by': self.env.user.id,
                'qc_approved_date': fields.Datetime.now(),
            })
            production.message_post(body=_(
                'QC Approval completed by %(user)s.'
            ) % {'user': self.env.user.display_name})
        return True

    def action_store_approval(self):
        """Step 2 — Store In-ward Approval (after QC, before Confirm)."""
        for production in self:
            if production.state != 'draft':
                raise UserError(_(
                    'Store Approval is only allowed on draft Manufacturing Order %(mo)s.'
                ) % {'mo': production.name})
            if production.mo_approval_state == 'pending_qc':
                raise UserError(_(
                    'Manufacturing Order %(mo)s must be approved by QC first.'
                ) % {'mo': production.name})
            if production.mo_approval_state != 'pending_store':
                raise UserError(_(
                    'Manufacturing Order %(mo)s is not waiting for Store approval.\n'
                    'Current status: %(status)s'
                ) % {
                    'mo': production.name,
                    'status': dict(production._fields['mo_approval_state'].selection).get(
                        production.mo_approval_state, production.mo_approval_state
                    ),
                })
            production.write({
                'mo_approval_state': 'approved',
                'store_approved_by': self.env.user.id,
                'store_approved_date': fields.Datetime.now(),
            })
            production.message_post(body=_(
                'Store In-ward Approval completed by %(user)s. MO can now be confirmed.'
            ) % {'user': self.env.user.display_name})
        return True
