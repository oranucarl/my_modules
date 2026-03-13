from odoo import api, fields, models
from datetime import timedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # HR Responsible
    hr_responsible_id = fields.Many2one(
        'res.users',
        string='HR Responsible',
        tracking=True
    )

    # Expatriate Documentation Fields
    document_type_id = fields.Many2one(
        'expatriate.document.type',
        string='Document Type'
    )
    sponsor_company_id = fields.Many2one(
        'expatriate.sponsor.company',
        string='Sponsoring Company'
    )
    document_number = fields.Char(
        string='Document Number'
    )
    document_expiry_date = fields.Date(
        string='Document Expiry Date',
        tracking=True
    )
    document_days_left = fields.Integer(
        string='Document Days Left',
        compute='_compute_document_days_left',
        store=True
    )
    document_alert_status = fields.Selection(
        [
            ('expired', 'Expired'),
            ('urgent', 'Urgent'),
            ('due_soon', 'Due Soon'),
            ('safe', 'Safe')
        ],
        string='Document Status',
        compute='_compute_document_alert_status',
        store=True
    )
    passport_number = fields.Char(
        string='Passport Number'
    )
    passport_expiry_date = fields.Date(
        string='Passport Expiration Date',
        tracking=True
    )
    passport_days_left = fields.Integer(
        string='Passport Days Left',
        compute='_compute_passport_days_left',
        store=True
    )

    # Computed field to check if contract is expatriate
    is_expatriate_contract = fields.Boolean(
        string='Is Expatriate Contract',
        compute='_compute_is_expatriate_contract',
        store=True
    )

    @api.depends('structure_type_id', 'structure_type_id.is_expatriate')
    def _compute_is_expatriate_contract(self):
        """Check if contract uses an expatriate structure type"""
        for contract in self:
            contract.is_expatriate_contract = contract.structure_type_id.is_expatriate if contract.structure_type_id else False

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-fill department and job from employee on contract creation"""
        for vals in vals_list:
            if vals.get('employee_id'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                # Only set if not already provided in vals
                if not vals.get('department_id') and employee.department_id:
                    vals['department_id'] = employee.department_id.id
                if not vals.get('job_id') and employee.job_id:
                    vals['job_id'] = employee.job_id.id
        return super().create(vals_list)

    @api.depends('document_expiry_date')
    def _compute_document_days_left(self):
        """Calculate days until document expiry"""
        for contract in self:
            if contract.document_expiry_date:
                delta = contract.document_expiry_date - fields.Date.today()
                contract.document_days_left = delta.days
            else:
                contract.document_days_left = 0

    @api.depends('passport_expiry_date')
    def _compute_passport_days_left(self):
        """Calculate days until passport expiry"""
        for contract in self:
            if contract.passport_expiry_date:
                delta = contract.passport_expiry_date - fields.Date.today()
                contract.passport_days_left = delta.days
            else:
                contract.passport_days_left = 0

    @api.depends('document_days_left', 'document_expiry_date')
    def _compute_document_alert_status(self):
        """Determine alert status based on days left"""
        for contract in self:
            if not contract.document_expiry_date:
                contract.document_alert_status = False
            elif contract.document_days_left < 0:
                contract.document_alert_status = 'expired'
            elif contract.document_days_left < 30:
                contract.document_alert_status = 'urgent'
            elif contract.document_days_left <= 60:
                contract.document_alert_status = 'due_soon'
            else:
                contract.document_alert_status = 'safe'

    def _send_expiry_notifications(self):
        """Send expiry notifications for contracts with HR responsible"""
        today = fields.Date.today()
        ten_days_later = today + timedelta(days=10)

        # Find contracts that need notification (10 days before or on expiry date)
        contracts_to_notify = self.search([
            ('hr_responsible_id', '!=', False),
            '|', '|', '|',
            ('date_end', 'in', [today, ten_days_later]),
            ('passport_expiry_date', 'in', [today, ten_days_later]),
            ('document_expiry_date', 'in', [today, ten_days_later]),
            ('date_end', '=', False)  # Always include to check other dates
        ])

        template = self.env.ref('pct_payroll_expatriate.email_template_contract_expiry_notification', raise_if_not_found=False)
        if not template:
            return

        for contract in contracts_to_notify:
            notifications = []

            # Check contract end date
            if contract.date_end:
                if contract.date_end == today:
                    notifications.append(f"Contract expires TODAY")
                elif contract.date_end == ten_days_later:
                    notifications.append(f"Contract expires in 10 days ({contract.date_end.strftime('%d-%b-%Y')})")

            # Check passport expiry
            if contract.passport_expiry_date:
                if contract.passport_expiry_date == today:
                    notifications.append(f"Passport expires TODAY")
                elif contract.passport_expiry_date == ten_days_later:
                    notifications.append(f"Passport expires in 10 days ({contract.passport_expiry_date.strftime('%d-%b-%Y')})")

            # Check document expiry
            if contract.document_expiry_date:
                if contract.document_expiry_date == today:
                    notifications.append(f"Document expires TODAY")
                elif contract.document_expiry_date == ten_days_later:
                    notifications.append(f"Document expires in 10 days ({contract.document_expiry_date.strftime('%d-%b-%Y')})")

            # Send email if there are notifications
            if notifications:
                template.with_context(
                    notifications=notifications
                ).send_mail(contract.id, force_send=True)
