from odoo import api, fields, models


class ExpatriateDocument(models.Model):
    _name = 'expatriate.document'
    _description = 'Expatriate Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'alert_status, days_left'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        domain="[('category_ids.is_expatriate', '=', True)]"
    )
    document_type = fields.Selection(
        [
            ('residence', 'Residence Permit'),
            ('cerpec', 'CERPEC'),
            ('work_permit', 'Work Permit'),
            ('visa', 'Visa'),
            ('other', 'Other')
        ],
        string='Document Type',
        required=True,
        default='residence'
    )
    sponsor_company_id = fields.Many2one(
        'expatriate.sponsor.company',
        string='Sponsoring Company'
    )
    designation = fields.Char(
        string='Designation'
    )
    passport_number = fields.Char(
        string='Passport Number'
    )
    passport_expiry = fields.Date(
        string='Passport Expiration Date'
    )
    passport_days_left = fields.Integer(
        string='Passport Days Left',
        compute='_compute_passport_days_left',
        store=True
    )
    document_number = fields.Char(
        string='Document Number'
    )
    expiry_date = fields.Date(
        string='Document Expiry Date',
        tracking=True
    )
    days_left = fields.Integer(
        string='Days Left',
        compute='_compute_days_left',
        store=True
    )
    alert_status = fields.Selection(
        [
            ('expired', 'Expired'),
            ('urgent', 'Urgent'),
            ('due_soon', 'Due Soon'),
            ('safe', 'Safe')
        ],
        string='Status',
        compute='_compute_alert_status',
        store=True
    )
    quota_status = fields.Selection(
        [
            ('old_quota', 'Old Quota'),
            ('new_quota', 'New Quota'),
            ('old_quota_gone', 'Old Quota (Gone)')
        ],
        string='Quota Status'
    )
    employment_status = fields.Selection(
        [
            ('active', 'Active'),
            ('left', 'Left'),
            ('not_renewed', 'Not Renewed')
        ],
        string='Employment Status',
        default='active'
    )
    active = fields.Boolean(
        default=True
    )
    notes = fields.Text(
        string='Notes'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    @api.depends('employee_id', 'document_type')
    def _compute_name(self):
        """Compute reference name from employee and document type"""
        for record in self:
            emp_name = record.employee_id.name or ''
            doc_type = dict(record._fields['document_type'].selection).get(
                record.document_type, ''
            )
            record.name = f"{emp_name} - {doc_type}".strip(' -')

    @api.depends('expiry_date')
    def _compute_days_left(self):
        """Calculate days until document expiry"""
        for record in self:
            if record.expiry_date:
                delta = record.expiry_date - fields.Date.today()
                record.days_left = delta.days
            else:
                record.days_left = 0

    @api.depends('passport_expiry')
    def _compute_passport_days_left(self):
        """Calculate days until passport expiry"""
        for record in self:
            if record.passport_expiry:
                delta = record.passport_expiry - fields.Date.today()
                record.passport_days_left = delta.days
            else:
                record.passport_days_left = 0

    @api.depends('days_left', 'expiry_date')
    def _compute_alert_status(self):
        """Determine alert status based on days left"""
        for record in self:
            if not record.expiry_date:
                record.alert_status = False
            elif record.days_left < 0:
                record.alert_status = 'expired'
            elif record.days_left < 30:
                record.alert_status = 'urgent'
            elif record.days_left <= 60:
                record.alert_status = 'due_soon'
            else:
                record.alert_status = 'safe'

    def cron_recompute_days(self):
        """Cron job to recompute days left for all active document records"""
        records = self.search([('active', '=', True)])
        records._compute_days_left()
