from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeCategory(models.Model):
    _inherit = 'hr.employee.category'

    is_expatriate = fields.Boolean(
        string='Expatriate Tag',
        default=False,
        help='Mark this tag as the expatriate identifier. '
             'Employees with this tag are considered expatriate staff.'
    )

    @api.constrains('is_expatriate')
    def _check_single_expatriate_tag(self):
        """Ensure only one tag can be marked as expatriate"""
        for record in self:
            if record.is_expatriate:
                existing = self.search([
                    ('is_expatriate', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f'Only one tag can be marked as expatriate. '
                        f'The tag "{existing[0].name}" is already marked as expatriate.'
                    )
