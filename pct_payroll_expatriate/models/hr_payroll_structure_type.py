from odoo import fields, models


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    is_expatriate = fields.Boolean(
        string='Expatriate',
        default=False,
        help='Check this box if this structure type is for expatriate employees. '
             'Contracts and payslips using this structure type will be restricted '
             'to users with Expatriate Payroll Manager access.',
    )
