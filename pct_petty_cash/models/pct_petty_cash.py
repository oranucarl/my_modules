# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class PctPettyCash(models.Model):
    _name = 'pct.petty.cash'
    _description = 'Petty Cash Custodian'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Petty Cash Name',
        required=True,
        tracking=True,
        help='Custodian project name',
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Draft: Setup phase, Running: Active operations, Closed: Year-end closed',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
    )
    custodian_id = fields.Many2one(
        'res.users',
        string='Custodian',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help='User responsible for this petty cash',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Petty Cash Journal',
        required=True,
        domain="[('type', '=', 'cash'), ('company_id', '=', company_id)]",
        tracking=True,
        help='Cash journal for custodian transactions',
    )
    custodian_account_id = fields.Many2one(
        'account.account',
        string='Custodian Account',
        compute='_compute_custodian_account',
        store=True,
        readonly=True,
        help='Cash GL account created for custodian (from journal)',
    )

    # Amounts
    amount_brought_forward = fields.Monetary(
        string='Amount Brought Forward',
        currency_field='currency_id',
        compute='_compute_amount_brought_forward',
        store=True,
        help='Balance from previous years (allocations - expenses before current year)',
    )
    amount_allocated = fields.Monetary(
        string='Amount Allocated (Current Year)',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help='Total amount allocated in current year',
    )
    amount_expensed = fields.Monetary(
        string='Amount Expensed (Current Year)',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help='Total amount expensed in current year',
    )
    amount_left = fields.Monetary(
        string='Amount Left',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help='Remaining balance (Brought Forward + Allocated - Expensed)',
    )

    # Lines
    allocation_line_ids = fields.One2many(
        'pct.petty.cash.allocation',
        'petty_cash_id',
        string='Allocation Lines',
    )
    expense_line_ids = fields.One2many(
        'pct.petty.cash.expense',
        'petty_cash_id',
        string='Expense Lines',
    )

    @api.depends('journal_id')
    def _compute_custodian_account(self):
        for record in self:
            if record.journal_id:
                record.custodian_account_id = record.journal_id.default_account_id
            else:
                record.custodian_account_id = False

    @api.depends(
        'allocation_line_ids.amount',
        'allocation_line_ids.state',
        'allocation_line_ids.payment_date',
        'expense_line_ids.amount',
        'expense_line_ids.state',
        'expense_line_ids.expense_date',
    )
    def _compute_amount_brought_forward(self):
        """Calculate balance from previous years (posted allocations - posted expenses before current year)"""
        current_year = date.today().year
        for record in self:
            # Sum allocations from previous years (only posted)
            prev_allocations = record.allocation_line_ids.filtered(
                lambda l: l.payment_date
                and l.payment_date.year < current_year
                and l.state == 'posted'
            )
            total_prev_allocated = sum(prev_allocations.mapped('amount'))

            # Sum expenses from previous years (only posted)
            prev_expenses = record.expense_line_ids.filtered(
                lambda l: l.expense_date
                and l.expense_date.year < current_year
                and l.state == 'posted'
            )
            total_prev_expensed = sum(prev_expenses.mapped('amount'))

            record.amount_brought_forward = total_prev_allocated - total_prev_expensed

    @api.depends(
        'amount_brought_forward',
        'allocation_line_ids.amount',
        'allocation_line_ids.state',
        'allocation_line_ids.payment_date',
        'expense_line_ids.amount',
        'expense_line_ids.state',
        'expense_line_ids.expense_date',
    )
    def _compute_amounts(self):
        current_year = date.today().year
        for record in self:
            # Sum allocations for current year (only posted)
            allocations = record.allocation_line_ids.filtered(
                lambda l: l.payment_date
                and l.payment_date.year == current_year
                and l.state == 'posted'
            )
            record.amount_allocated = sum(allocations.mapped('amount'))

            # Sum expenses for current year (only posted)
            expenses = record.expense_line_ids.filtered(
                lambda l: l.expense_date
                and l.expense_date.year == current_year
                and l.state == 'posted'
            )
            record.amount_expensed = sum(expenses.mapped('amount'))

            # Calculate remaining
            record.amount_left = (
                record.amount_brought_forward
                + record.amount_allocated
                - record.amount_expensed
            )

    def action_set_running(self):
        """Set petty cash to running state"""
        for record in self:
            if record.state == 'draft':
                record.state = 'running'

    def action_set_closed(self):
        """Set petty cash to closed state"""
        for record in self:
            if record.state == 'running':
                record.state = 'closed'

    def action_set_draft(self):
        """Reset petty cash to draft state"""
        for record in self:
            record.state = 'draft'

    @api.model
    def _get_current_year_domain(self):
        """Helper to get domain for current year records"""
        current_year = date.today().year
        return [
            ('payment_date', '>=', date(current_year, 1, 1)),
            ('payment_date', '<=', date(current_year, 12, 31)),
        ]


class PctPettyCashAllocation(models.Model):
    _name = 'pct.petty.cash.allocation'
    _description = 'Petty Cash Allocation Line'
    _order = 'payment_date desc, id desc'
    _inherit = 'analytic.mixin'

    petty_cash_id = fields.Many2one(
        'pct.petty.cash',
        string='Petty Cash',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='petty_cash_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        related='petty_cash_id.currency_id',
        store=True,
    )
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(
        string='Amount Allocated',
        currency_field='currency_id',
        required=True,
    )
    source_journal_id = fields.Many2one(
        'account.journal',
        string='Source Journal',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        help='Company bank/cash journal from which payment is made',
    )
    source_account_id = fields.Many2one(
        'account.account',
        string='Source Account',
        compute='_compute_source_account',
        store=True,
        help='Account from source journal',
    )
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
    )

    @api.depends('move_id', 'move_id.state')
    def _compute_state(self):
        for line in self:
            if line.move_id:
                line.state = line.move_id.state
            else:
                line.state = 'draft'

    @api.depends('source_journal_id')
    def _compute_source_account(self):
        for line in self:
            if line.source_journal_id:
                line.source_account_id = line.source_journal_id.default_account_id
            else:
                line.source_account_id = False

    def action_create_move(self):
        """Create journal entry for allocation"""
        self.ensure_one()
        if self.move_id:
            raise UserError(_('Journal entry already exists for this allocation.'))

        petty_cash = self.petty_cash_id
        if not petty_cash.custodian_account_id:
            raise UserError(_('Please configure a custodian account on the petty cash journal.'))
        if not self.source_account_id:
            raise UserError(_('Please select a source journal with a default account.'))

        # Get custodian's partner_id
        partner_id = petty_cash.custodian_id.partner_id.id if petty_cash.custodian_id.partner_id else False

        move_vals = {
            'move_type': 'entry',
            'journal_id': petty_cash.journal_id.id,
            'date': self.payment_date,
            'ref': _('Petty Cash Allocation: %s') % petty_cash.name,
            'line_ids': [
                Command.create({
                    'account_id': petty_cash.custodian_account_id.id,
                    'partner_id': partner_id,
                    'debit': self.amount,
                    'credit': 0,
                    'name': _('Petty Cash Allocation'),
                    'analytic_distribution': self.analytic_distribution,
                }),
                Command.create({
                    'account_id': self.source_account_id.id,
                    'partner_id': partner_id,
                    'debit': 0,
                    'credit': self.amount,
                    'name': _('Petty Cash Allocation from %s') % self.source_journal_id.name,
                    'analytic_distribution': self.analytic_distribution,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        self.move_id = move.id
        return True

    def action_post(self):
        """Post the journal entry"""
        for line in self:
            if not line.move_id:
                line.action_create_move()
            if line.move_id.state == 'draft':
                line.move_id.action_post()
        return True

    def action_view_move(self):
        """View the journal entry"""
        self.ensure_one()
        if not self.move_id:
            raise UserError(_('No journal entry exists for this allocation.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class PctPettyCashExpense(models.Model):
    _name = 'pct.petty.cash.expense'
    _description = 'Petty Cash Expense Line'
    _order = 'expense_date desc, id desc'
    _inherit = 'analytic.mixin'

    petty_cash_id = fields.Many2one(
        'pct.petty.cash',
        string='Petty Cash',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='petty_cash_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        related='petty_cash_id.currency_id',
        store=True,
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
    account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        compute='_compute_account',
        store=True,
        readonly=False,
        help='Expense account (from product category)',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'pct_petty_cash_expense_attachment_rel',
        'expense_id',
        'attachment_id',
        string='Receipts',
        help='Attach receipt documents for this expense',
    )
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
    )

    @api.depends('move_id', 'move_id.state')
    def _compute_state(self):
        for line in self:
            if line.move_id:
                line.state = line.move_id.state
            else:
                line.state = 'draft'

    @api.depends('product_id')
    def _compute_account(self):
        for line in self:
            if line.product_id:
                # Get expense account from product or category
                accounts = line.product_id.product_tmpl_id.get_product_accounts()
                line.account_id = accounts.get('expense') or False
            else:
                line.account_id = False

    def action_create_move(self):
        """Create journal entry for expense"""
        self.ensure_one()
        if self.move_id:
            raise UserError(_('Journal entry already exists for this expense.'))

        petty_cash = self.petty_cash_id
        if not petty_cash.custodian_account_id:
            raise UserError(_('Please configure a custodian account on the petty cash journal.'))
        if not self.account_id:
            raise UserError(_('Please select an expense account.'))

        # Get custodian's partner_id
        partner_id = petty_cash.custodian_id.partner_id.id if petty_cash.custodian_id.partner_id else False

        # Build debit line values
        debit_line_vals = {
            'account_id': self.account_id.id,
            'partner_id': partner_id,
            'debit': self.amount,
            'credit': 0,
            'name': self.description,
            'analytic_distribution': self.analytic_distribution,
        }
        if self.product_id:
            debit_line_vals['product_id'] = self.product_id.id

        move_vals = {
            'move_type': 'entry',
            'journal_id': petty_cash.journal_id.id,
            'date': self.expense_date,
            'ref': _('Petty Cash Expense: %s - %s') % (petty_cash.name, self.description),
            'line_ids': [
                Command.create(debit_line_vals),
                Command.create({
                    'account_id': petty_cash.custodian_account_id.id,
                    'partner_id': partner_id,
                    'debit': 0,
                    'credit': self.amount,
                    'name': _('Petty Cash Expense: %s') % self.description,
                    'analytic_distribution': self.analytic_distribution,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        self.move_id = move.id
        return True

    def action_post(self):
        """Post the journal entry"""
        for line in self:
            if line.petty_cash_id.state != 'running':
                raise UserError(_('Cannot post expense. The petty cash "%s" must be in Running state.') % line.petty_cash_id.name)
            if not line.move_id:
                line.action_create_move()
            if line.move_id.state == 'draft':
                line.move_id.action_post()
        return True

    def action_view_move(self):
        """View the journal entry"""
        self.ensure_one()
        if not self.move_id:
            raise UserError(_('No journal entry exists for this expense.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_form(self):
        """Open expense line in form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expense Details'),
            'res_model': 'pct.petty.cash.expense',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
