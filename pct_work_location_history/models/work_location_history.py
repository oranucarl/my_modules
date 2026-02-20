from odoo import api, fields, models


class WorkLocationHistory(models.Model):
    _name = 'hr.work.location.history'
    _description = 'Employee Work Location History'
    _order = 'change_date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    work_location_id = fields.Many2one(
        'hr.work.location',
        string='Work Location',
        required=True,
        ondelete='restrict',
        index=True,
    )
    previous_work_location_id = fields.Many2one(
        'hr.work.location',
        string='Previous Work Location',
        ondelete='set null',
    )
    change_date = fields.Datetime(
        string='Change Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    changed_by_id = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        default=lambda self: self.env.user,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        related='employee_id.company_id',
        string='Company',
        store=True,
        index=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department',
        store=True,
    )
    duration = fields.Float(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True,
        help='Duration at this work location in days',
    )
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration',
        store=True,
    )
    is_current = fields.Boolean(
        string='Current Location',
        compute='_compute_is_current',
        store=True,
    )
    notes = fields.Text(string='Notes')
    employee_count = fields.Integer(
        string='Count',
        default=1,
        store=True,
        help='Used for counting employees in reports',
    )

    @api.depends('employee_id', 'change_date')
    def _compute_is_current(self):
        for record in self:
            if not record.employee_id or not record.change_date:
                record.is_current = False
                continue
            latest = self.search([
                ('employee_id', '=', record.employee_id.id),
            ], order='change_date desc', limit=1)
            record.is_current = latest.id == record.id

    @api.depends('employee_id', 'change_date', 'is_current')
    def _compute_duration(self):
        for record in self:
            if not record.employee_id or not record.change_date:
                record.duration = 0.0
                record.duration_display = ''
                continue

            next_record = self.search([
                ('employee_id', '=', record.employee_id.id),
                ('change_date', '>', record.change_date),
            ], order='change_date asc', limit=1)

            if next_record:
                end_date = next_record.change_date
            else:
                end_date = fields.Datetime.now()

            delta = end_date - record.change_date
            total_seconds = delta.total_seconds()
            days = total_seconds / 86400
            record.duration = round(days, 2)

            total_days = int(days)
            hours = int((total_seconds % 86400) / 3600)
            minutes = int((total_seconds % 3600) / 60)

            if total_days > 0:
                record.duration_display = f"{total_days}d {hours}h {minutes}m"
            elif hours > 0:
                record.duration_display = f"{hours}h {minutes}m"
            else:
                record.duration_display = f"{minutes}m"

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.employee_id.name} - {record.work_location_id.name} ({record.change_date.strftime('%Y-%m-%d %H:%M')})"
            result.append((record.id, name))
        return result

    @api.model
    def _recompute_all_durations(self):
        """Recompute durations for all records."""
        all_records = self.search([])
        all_records._compute_duration()
        all_records._compute_is_current()
