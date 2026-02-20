from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    work_location_history_ids = fields.One2many(
        'hr.work.location.history',
        'employee_id',
        string='Work Location History',
    )
    work_location_history_count = fields.Integer(
        string='Work Location History Count',
        compute='_compute_work_location_history_count',
    )

    @api.depends('work_location_history_ids')
    def _compute_work_location_history_count(self):
        for employee in self:
            employee.work_location_history_count = len(employee.work_location_history_ids)

    def write(self, vals):
        if 'work_location_id' in vals:
            for employee in self:
                new_location_id = vals.get('work_location_id')
                old_location_id = employee.work_location_id.id if employee.work_location_id else False

                if new_location_id != old_location_id:
                    self.env['hr.work.location.history'].create({
                        'employee_id': employee.id,
                        'work_location_id': new_location_id,
                        'previous_work_location_id': old_location_id,
                        'change_date': fields.Datetime.now(),
                        'changed_by_id': self.env.user.id,
                    })
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee, vals in zip(employees, vals_list):
            if vals.get('work_location_id'):
                self.env['hr.work.location.history'].create({
                    'employee_id': employee.id,
                    'work_location_id': vals['work_location_id'],
                    'previous_work_location_id': False,
                    'change_date': fields.Datetime.now(),
                    'changed_by_id': self.env.user.id,
                })
        return employees

    def action_view_work_location_history(self):
        self.ensure_one()
        return {
            'name': f'Work Location History - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.work.location.history',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'search_default_employee_id': self.id,
            },
        }
