# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PctPettyCashExpenseWizard(models.TransientModel):
    _name = 'pct.petty.cash.expense.wizard'
    _description = 'Petty Cash Expense Wizard'
    _inherit = ['analytic.mixin']

    # Analytic plan IDs for project and project stage
    PROJECT_PLAN_ID = 1
    PROJECT_STAGE_PLAN_ID = 2

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
    description = fields.Char(
        string='Description',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Expense Category',
        domain="[('type', '=', 'service')]",
        help='Product/service representing the expense category',
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
        help='Attach receipt documents for this expense (PDF or PNG only)',
    )

    # Allowed file types for receipts (pictures and PDF)
    ALLOWED_MIMETYPES = [
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/tiff',
        'image/bmp',
    ]
    ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.tiff', '.tif', '.bmp']

    @api.constrains('attachment_ids')
    def _check_attachment_file_types(self):
        """Validate that attachments are only picture or PDF files"""
        for wizard in self:
            for attachment in wizard.attachment_ids:
                is_valid = False
                # Check mimetype
                if attachment.mimetype:
                    if attachment.mimetype in self.ALLOWED_MIMETYPES:
                        is_valid = True
                    elif attachment.mimetype.startswith('image/'):
                        is_valid = True
                # Also check file extension as fallback
                if not is_valid and attachment.name:
                    file_ext = '.' + attachment.name.split('.')[-1].lower() if '.' in attachment.name else ''
                    if file_ext in self.ALLOWED_EXTENSIONS:
                        is_valid = True
                if not is_valid and attachment.mimetype:
                    raise ValidationError(_(
                        'Invalid file type for receipt "%s". Only Picture and PDF files are allowed.'
                    ) % attachment.name)

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
                raise ValidationError(_('Analytic distribution is required for expense records.'))

    def _validate_analytic_distribution(self):
        """Validate analytic distribution has project and project stage"""
        self.ensure_one()
        if not self.analytic_distribution:
            raise UserError(_('Analytic distribution is required for expense records.'))

        # Get analytic accounts from distribution
        # Keys can be single IDs or comma-separated IDs (e.g., '242' or '242,410')
        analytic_account_ids = set()
        for key in self.analytic_distribution.keys():
            for aid in str(key).split(','):
                analytic_account_ids.add(int(aid.strip()))

        if not analytic_account_ids:
            raise UserError(_('Analytic distribution is required for expense records.'))

        # Check for project and project stage analytic accounts
        analytic_accounts = self.env['account.analytic.account'].browse(list(analytic_account_ids))

        has_project = False
        has_project_stage = False

        for account in analytic_accounts:
            if account.plan_id.id == self.PROJECT_PLAN_ID:
                has_project = True
            if account.plan_id.id == self.PROJECT_STAGE_PLAN_ID:
                has_project_stage = True

        if not has_project:
            raise UserError(_('Please select a Project in the analytic distribution.'))
        if not has_project_stage:
            raise UserError(_('Please select a Project Stage in the analytic distribution.'))

    def _send_expense_notification(self, expense):
        """Send email notification to accounting team for new expense"""
        notification_email = self.env['ir.config_parameter'].sudo().get_param(
            'pct_petty_cash.notification_email'
        )
        if not notification_email:
            return

        template = self.env.ref('pct_petty_cash.mail_template_expense_notification', raise_if_not_found=False)
        if template:
            # Generate email values from template
            email_values = {
                'email_to': notification_email,
                'email_from': self.env.company.email or self.env.user.email_formatted,
            }
            template.send_mail(
                expense.id,
                force_send=True,
                email_values=email_values,
            )

    def action_create_expense(self):
        """Create expense line from wizard"""
        self.ensure_one()
        if self.petty_cash_id.state == 'closed':
            raise UserError(_('Cannot add expenses to a closed petty cash.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be greater than zero.'))
        if not self.analytic_distribution:
            raise UserError(_('Analytic distribution is required for expense records.'))

        # Validate project and project stage in analytic distribution
        self._validate_analytic_distribution()

        expense_vals = {
            'petty_cash_id': self.petty_cash_id.id,
            'expense_date': self.expense_date,
            'description': self.description,
            'product_id': self.product_id.id if self.product_id else False,
            'amount': self.amount,
            'analytic_distribution': self.analytic_distribution,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)] if self.attachment_ids else False,
        }
        expense = self.env['pct.petty.cash.expense'].create(expense_vals)

        # Send notification email to accounting team
        self._send_expense_notification(expense)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Petty Cash'),
            'res_model': 'pct.petty.cash',
            'res_id': self.petty_cash_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
