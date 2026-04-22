from odoo import api, fields, models


class ExpatriateHousing(models.Model):
    _name = 'expatriate.housing'
    _description = 'Expatriate Housing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'alert_status, days_to_expire'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'expatriate_housing_employee_rel',
        'housing_id',
        'employee_id',
        string='Employees',
        required=True,
        tracking=True,
        domain="[('category_ids.is_expatriate', '=', True)]"
    )
    employee_count = fields.Integer(
        string='Employee Count',
        compute='_compute_employee_count',
        store=True
    )
    location = fields.Char(
        string='Apartment Location',
        required=True
    )
    housing_type = fields.Char(
        string='Apartment Type'
    )
    contract_start_date = fields.Date(
        string='Contract Start Date',
        tracking=True
    )
    contract_end_date = fields.Date(
        string='Contract End Date',
        tracking=True
    )
    days_to_expire = fields.Integer(
        string='Days to Expire',
        compute='_compute_days_to_expire',
        store=True
    )
    alert_status = fields.Selection(
        [
            ('expired', 'Expired'),
            ('urgent', 'Urgent'),
            ('due_soon', 'Due Soon'),
            ('safe', 'Safe')
        ],
        string='Alert Status',
        compute='_compute_alert_status',
        store=True
    )

    # Housing Cost Line Items
    cost_line_ids = fields.One2many(
        'housing.cost.line',
        'housing_id',
        string='Cost Items'
    )

    total_cost = fields.Monetary(
        string='Total Housing Cost',
        compute='_compute_total_cost',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    active = fields.Boolean(
        default=True
    )
    available_assets = fields.Html(
        string='Available Assets'
    )
    notes = fields.Text(
        string='Notes'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    @api.depends('employee_ids', 'location')
    def _compute_name(self):
        """Compute reference name from employees and location"""
        for record in self:
            if record.employee_ids:
                if len(record.employee_ids) == 1:
                    emp_name = record.employee_ids[0].name
                else:
                    emp_name = f"{record.employee_ids[0].name} +{len(record.employee_ids) - 1}"
            else:
                emp_name = ''
            location = record.location or ''
            record.name = f"{emp_name} - {location}".strip(' -')

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        """Compute number of employees in housing"""
        for record in self:
            record.employee_count = len(record.employee_ids)

    @api.depends('contract_end_date')
    def _compute_days_to_expire(self):
        """Calculate days until contract end date"""
        for record in self:
            if record.contract_end_date:
                delta = record.contract_end_date - fields.Date.today()
                record.days_to_expire = delta.days
            else:
                record.days_to_expire = 0

    @api.depends('days_to_expire', 'contract_end_date')
    def _compute_alert_status(self):
        """Determine alert status based on days to expire"""
        for record in self:
            if not record.contract_end_date:
                record.alert_status = False
            elif record.days_to_expire < 0:
                record.alert_status = 'expired'
            elif record.days_to_expire < 30:
                record.alert_status = 'urgent'
            elif record.days_to_expire <= 60:
                record.alert_status = 'due_soon'
            else:
                record.alert_status = 'safe'

    @api.depends('cost_line_ids', 'cost_line_ids.amount')
    def _compute_total_cost(self):
        """Calculate total housing cost from line items"""
        for record in self:
            record.total_cost = sum(record.cost_line_ids.mapped('amount'))

    def cron_recompute_days(self):
        """Cron job to recompute days to expire for all active housing records"""
        records = self.search([('active', '=', True)])
        records._compute_days_to_expire()

    def action_export_housing_report(self):
        """Export housing report to Excel

        If called with selected records, exports only those.
        If called without selection (from header button), exports all records.
        """
        # Get selected records from context or use all visible records
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            housing_ids = active_ids
        else:
            # No selection - export all records matching the current search
            housing_ids = self.search([]).ids

        return {
            'type': 'ir.actions.act_window',
            'name': 'Export Housing Report',
            'res_model': 'housing.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_housing_ids': [(6, 0, housing_ids)]
            }
        }
