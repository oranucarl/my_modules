from odoo import api, fields, models


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    structure_id = fields.Many2one(
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Default to expatriate structure for expatriate payroll managers
        if self.env.user.has_group('pct_payroll_expatriate.group_hr_payroll_expatriate'):
            expatriate_structure = self.env['hr.payroll.structure'].search([
                ('type_id.is_expatriate', '=', True)
            ], limit=1)
            if expatriate_structure and 'structure_id' in fields_list:
                res['structure_id'] = expatriate_structure.id
        return res

    @api.model
    def _get_structure_domain(self):
        """Return domain for structure_id based on user's access rights."""
        if self.env.user.has_group('pct_payroll_expatriate.group_hr_payroll_expatriate'):
            # Expatriate managers can see all structures
            return []
        else:
            # Regular users can only see non-expatriate structures
            return [('type_id.is_expatriate', '!=', True)]

    @api.onchange('structure_id')
    def _onchange_structure_id(self):
        """Apply domain filter on structure_id based on user access."""
        domain = self._get_structure_domain()
        return {'domain': {'structure_id': domain}}

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override to apply domain on structure_id field."""
        res = super().fields_get(allfields, attributes)
        if 'structure_id' in res:
            domain = self._get_structure_domain()
            if domain:
                res['structure_id']['domain'] = str(domain)
        return res
