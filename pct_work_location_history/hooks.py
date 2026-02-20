from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    """Create initial work location history records for existing employees."""
    employees = env['hr.employee'].search([
        ('work_location_id', '!=', False),
    ])

    history_model = env['hr.work.location.history']

    for employee in employees:
        existing = history_model.search([
            ('employee_id', '=', employee.id),
        ], limit=1)

        if not existing:
            history_model.create({
                'employee_id': employee.id,
                'work_location_id': employee.work_location_id.id,
                'previous_work_location_id': False,
                'change_date': employee.write_date or employee.create_date,
                'changed_by_id': SUPERUSER_ID,
                'notes': 'Initial work location (created by module installation)',
            })
