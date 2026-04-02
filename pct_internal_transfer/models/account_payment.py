# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Extend payment_type to add 'transfer' option
    payment_type = fields.Selection(
        selection_add=[('transfer', 'Internal Transfer')],
        ondelete={'transfer': 'set default'}
    )

    # Destination journal for internal transfers
    destination_journal_id = fields.Many2one(
        'account.journal',
        string='Destination Journal',
        domain="[('type', 'in', ['bank', 'cash']), ('id', '!=', journal_id), ('company_id', '=', company_id)]",
        help="The bank/cash journal to transfer funds to."
    )

    @api.constrains('payment_type', 'destination_journal_id')
    def _check_destination_journal(self):
        for payment in self:
            if payment.payment_type == 'transfer' and not payment.destination_journal_id:
                raise ValidationError(_("Destination Journal is required for Internal Transfers."))
            if payment.payment_type == 'transfer' and payment.destination_journal_id == payment.journal_id:
                raise ValidationError(_("Destination Journal must be different from the source Journal."))

    @api.onchange('payment_type')
    def _onchange_payment_type_transfer(self):
        """Clear destination journal when payment type changes away from transfer."""
        if self.payment_type != 'transfer':
            self.destination_journal_id = False

    def _get_valid_liquidity_accounts(self):
        """Override to include destination journal account for internal transfers."""
        res = super()._get_valid_liquidity_accounts()
        if self.payment_type == 'transfer' and self.destination_journal_id:
            res |= self.destination_journal_id.default_account_id
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """Override to create direct bank-to-bank entries for internal transfers."""
        self.ensure_one()

        if self.payment_type != 'transfer':
            return super()._prepare_move_line_default_vals(write_off_line_vals, force_balance)

        # For internal transfers: direct debit destination bank, credit source bank
        source_account = self.journal_id.default_account_id
        dest_account = self.destination_journal_id.default_account_id

        if not source_account:
            raise ValidationError(
                _("Source journal '%s' does not have a default account configured.") % self.journal_id.name
            )
        if not dest_account:
            raise ValidationError(
                _("Destination journal '%s' does not have a default account configured.") % self.destination_journal_id.name
            )

        # Get amount in company currency
        if self.currency_id == self.company_id.currency_id:
            balance = self.amount
            amount_currency = self.amount
        else:
            amount_currency = self.amount
            balance = self.currency_id._convert(
                self.amount,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )

        # Get analytic distribution from project if available
        analytic_distribution = False
        if hasattr(self, 'project_id') and self.project_id and hasattr(self.project_id, '_get_analytic_distribution'):
            analytic_distribution = self.project_id._get_analytic_distribution()

        line_vals_list = [
            # Credit source bank (money out)
            {
                'name': _("Transfer to %s") % self.destination_journal_id.name,
                'date_maturity': self.date,
                'amount_currency': -amount_currency,
                'currency_id': self.currency_id.id,
                'debit': 0.0,
                'credit': balance,
                'partner_id': self.partner_id.id or False,
                'account_id': source_account.id,
                'analytic_distribution': analytic_distribution,
            },
            # Debit destination bank (money in)
            {
                'name': _("Transfer from %s") % self.journal_id.name,
                'date_maturity': self.date,
                'amount_currency': amount_currency,
                'currency_id': self.currency_id.id,
                'debit': balance,
                'credit': 0.0,
                'partner_id': self.partner_id.id or False,
                'account_id': dest_account.id,
                'analytic_distribution': analytic_distribution,
            },
        ]

        return line_vals_list

    def _synchronize_to_moves(self, changed_fields):
        """Extend to sync destination_journal_id changes."""
        res = super()._synchronize_to_moves(changed_fields)

        # If destination journal changed for transfers, regenerate move lines
        if 'destination_journal_id' in changed_fields:
            for payment in self.filtered(lambda p: p.payment_type == 'transfer' and p.move_id):
                # Update the move lines
                liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                line_vals = payment._prepare_move_line_default_vals()
                if len(line_vals) >= 2:
                    # Update source line (credit)
                    if liquidity_lines:
                        liquidity_lines[0].write({
                            'account_id': line_vals[0]['account_id'],
                            'name': line_vals[0]['name'],
                        })
                    # Update destination line (debit)
                    if counterpart_lines:
                        counterpart_lines[0].write({
                            'account_id': line_vals[1]['account_id'],
                            'name': line_vals[1]['name'],
                        })

        return res

    def _seek_for_lines(self):
        """Override to correctly identify lines for internal transfers."""
        self.ensure_one()

        if self.payment_type != 'transfer':
            return super()._seek_for_lines()

        # For transfers, we have source bank (liquidity) and destination bank (counterpart)
        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        source_account = self.journal_id.default_account_id
        dest_account = self.destination_journal_id.default_account_id if self.destination_journal_id else False

        for line in self.move_id.line_ids:
            if line.account_id == source_account:
                liquidity_lines += line
            elif dest_account and line.account_id == dest_account:
                counterpart_lines += line
            else:
                writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines

    def action_draft(self):
        """Override to handle resetting payment to draft, including cancelled journal entries."""
        self.state = 'draft'
        for payment in self:
            if payment.move_id:
                # Handle both posted and cancelled moves
                if payment.move_id.state in ('posted', 'cancel'):
                    payment.move_id.button_draft()

    def action_cancel(self):
        """Override to cancel and delete the journal entry."""
        self.state = 'canceled'
        for payment in self:
            if payment.move_id:
                move = payment.move_id
                # Unlink move from payment first
                payment.move_id = False
                # Reset to draft if posted, then delete
                if move.state == 'posted':
                    move.button_draft()
                move.unlink()

    def unlink(self):
        """Override to handle deletion - cancel moves instead of deleting to avoid audit trail error."""
        for payment in self:
            if payment.move_id:
                move = payment.move_id
                # Unlink the move from payment first
                payment.move_id = False
                # Reset to draft if needed, then cancel
                if move.state == 'posted':
                    move.button_draft()
                if move.state == 'draft':
                    move.button_cancel()
                # Try to delete, but if audit trail prevents it, just leave it cancelled
                try:
                    move.with_context(force_delete=True).unlink()
                except Exception:
                    # If deletion fails due to audit trail, the move stays cancelled
                    pass
        return super().unlink()
