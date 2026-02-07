# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PctPettyCashAllocationWizard(models.TransientModel):
    _name = 'pct.petty.cash.allocation.wizard'
    _description = 'Petty Cash Allocation Request Wizard'
    _inherit = ['analytic.mixin']

    petty_cash_id = fields.Many2one(
        'pct.petty.cash',
        string='Petty Cash',
        required=True,
        default=lambda self: self._default_petty_cash(),
    )
    company_id = fields.Many2one(
        related='petty_cash_id.company_id',
    )
    currency_id = fields.Many2one(
        related='petty_cash_id.currency_id',
    )
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(
        string='Amount Requested',
        currency_field='currency_id',
        required=True,
    )
    source_journal_id = fields.Many2one(
        'account.journal',
        string='Source Journal',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        help='Company bank/cash journal from which payment will be made',
    )

    @api.model
    def _default_petty_cash(self):
        """Get petty cash from context or find user's petty cash"""
        if self.env.context.get('active_model') == 'pct.petty.cash':
            return self.env.context.get('active_id')
        # Find petty cash where current user is custodian
        petty_cash = self.env['pct.petty.cash'].search([
            ('custodian_id', '=', self.env.user.id),
        ], limit=1)
        return petty_cash.id if petty_cash else False

    def action_create_allocation(self):
        """Create allocation line from wizard"""
        self.ensure_one()
        if self.petty_cash_id.state == 'closed':
            raise UserError(_('Cannot add allocations to a closed petty cash.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be greater than zero.'))

        allocation_vals = {
            'petty_cash_id': self.petty_cash_id.id,
            'payment_date': self.payment_date,
            'amount': self.amount,
            'source_journal_id': self.source_journal_id.id,
            'analytic_distribution': self.analytic_distribution,
        }
        self.env['pct.petty.cash.allocation'].create(allocation_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Petty Cash'),
            'res_model': 'pct.petty.cash',
            'res_id': self.petty_cash_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
