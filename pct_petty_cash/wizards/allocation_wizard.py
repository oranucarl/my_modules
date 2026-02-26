# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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
    request_date = fields.Date(
        string='Request Date',
        readonly=True,
        default=fields.Date.context_today,
        help='Date the allocation request is created (auto-set)',
    )
    amount = fields.Monetary(
        string='Amount Requested',
        currency_field='currency_id',
        required=True,
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

    @api.constrains('analytic_distribution')
    def _check_analytic_distribution(self):
        """Validate that analytic distribution is set"""
        for wizard in self:
            if not wizard.analytic_distribution:
                raise ValidationError(_('Analytic distribution is required for allocation requests.'))

    def _send_allocation_notification(self, allocation):
        """Send email notification to accounting team for new allocation"""
        notification_email = self.env['ir.config_parameter'].sudo().get_param(
            'pct_petty_cash.notification_email'
        )
        if not notification_email:
            return

        template = self.env.ref('pct_petty_cash.mail_template_allocation_notification', raise_if_not_found=False)
        if template:
            # Generate email values from template
            email_values = {
                'email_to': notification_email,
                'email_from': self.env.company.email or self.env.user.email_formatted,
            }
            template.send_mail(
                allocation.id,
                force_send=True,
                email_values=email_values,
            )

    def action_create_allocation(self):
        """Create allocation line from wizard"""
        self.ensure_one()
        if self.petty_cash_id.state == 'closed':
            raise UserError(_('Cannot add allocations to a closed petty cash.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be greater than zero.'))
        if not self.analytic_distribution:
            raise UserError(_('Analytic distribution is required for allocation requests.'))

        allocation_vals = {
            'petty_cash_id': self.petty_cash_id.id,
            'request_date': self.request_date or fields.Date.context_today(self),
            'amount': self.amount,
            'analytic_distribution': self.analytic_distribution,
        }
        allocation = self.env['pct.petty.cash.allocation'].create(allocation_vals)

        # Send notification email to accounting team
        self._send_allocation_notification(allocation)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Petty Cash'),
            'res_model': 'pct.petty.cash',
            'res_id': self.petty_cash_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
