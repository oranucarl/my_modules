# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="The branch this employee belongs to."
    )


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        related='employee_id.branch_id',
        help="Branch this employee belongs to (for POS visibility)."
    )
