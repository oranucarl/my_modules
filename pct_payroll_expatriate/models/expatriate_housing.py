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
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        domain="[('category_ids.is_expatriate', '=', True)]"
    )
    location = fields.Char(
        string='Location / Address',
        required=True
    )
    housing_type = fields.Char(
        string='Type'
    )
    renewal_date = fields.Date(
        string='Date of Renewal',
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
    notes = fields.Text(
        string='Notes'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    @api.depends('employee_id', 'location')
    def _compute_name(self):
        """Compute reference name from employee and location"""
        for record in self:
            emp_name = record.employee_id.name or ''
            location = record.location or ''
            record.name = f"{emp_name} - {location}".strip(' -')

    @api.depends('renewal_date')
    def _compute_days_to_expire(self):
        """Calculate days until renewal date"""
        for record in self:
            if record.renewal_date:
                delta = record.renewal_date - fields.Date.today()
                record.days_to_expire = delta.days
            else:
                record.days_to_expire = 0

    @api.depends('days_to_expire', 'renewal_date')
    def _compute_alert_status(self):
        """Determine alert status based on days to expire"""
        for record in self:
            if not record.renewal_date:
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
