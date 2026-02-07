# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PctPettyCashExpenseWizard(models.TransientModel):
    _name = 'pct.petty.cash.expense.wizard'
    _description = 'Petty Cash Expense Wizard'
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
    expense_date = fields.Date(
        string='Expense Date',
        required=True,
        default=fields.Date.context_today,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Expense Category',
        domain="[('type', '=', 'service')]",
        help='Product/service representing the expense category',
    )
    description = fields.Char(
        string='Description',
        required=True,
    )
    amount = fields.Monetary(
        string='Amount Spent',
        currency_field='currency_id',
        required=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'pct_petty_cash_expense_wizard_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Receipts',
        help='Attach receipt documents for this expense',
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

    def action_create_expense(self):
        """Create expense line from wizard"""
        self.ensure_one()
        if self.petty_cash_id.state == 'closed':
            raise UserError(_('Cannot add expenses to a closed petty cash.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be greater than zero.'))

        expense_vals = {
            'petty_cash_id': self.petty_cash_id.id,
            'expense_date': self.expense_date,
            'description': self.description,
            'amount': self.amount,
            'analytic_distribution': self.analytic_distribution,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)] if self.attachment_ids else False,
        }
        if self.product_id:
            expense_vals['product_id'] = self.product_id.id
        self.env['pct.petty.cash.expense'].create(expense_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Petty Cash'),
            'res_model': 'pct.petty.cash',
            'res_id': self.petty_cash_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
