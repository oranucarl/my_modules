from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ExpatriateAllowance(models.Model):
    _name = 'expatriate.allowance'
    _description = 'Expatriate Allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        readonly=True,
        default='New',
        copy=False
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        domain="[('category_ids.is_expatriate', '=', True)]"
    )
    job_id = fields.Many2one(
        related='employee_id.job_id',
        string='Position',
        store=True,
        readonly=True
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )
    construction_site = fields.Char(
        string='Construction Site'
    )
    date = fields.Date(
        string='Allowance Date',
        required=True,
        tracking=True,
        default=fields.Date.context_today
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    bank_name = fields.Char(
        string='Bank'
    )
    bank_account_number = fields.Char(
        string='Account Number'
    )
    paid_from_account = fields.Char(
        string='Paid from Account'
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('paid', 'Paid')
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    notes = fields.Text(
        string='Notes'
    )

    @api.constrains('amount')
    def _check_amount_positive(self):
        """Ensure amount is positive"""
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Allowance amount must be greater than zero.')

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for new records"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'expatriate.allowance'
                ) or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the allowance"""
        self.write({'state': 'confirmed'})

    def action_pay(self):
        """Mark the allowance as paid"""
        self.write({'state': 'paid'})

    def action_reset_draft(self):
        """Reset allowance to draft"""
        self.write({'state': 'draft'})
