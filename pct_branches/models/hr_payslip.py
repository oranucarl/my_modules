# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslip, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('employee_id')
    def _onchange_employee_branch(self):
        if self.employee_id and self.employee_id.branch_id:
            self.branch_id = self.employee_id.branch_id


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslipRun, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res
