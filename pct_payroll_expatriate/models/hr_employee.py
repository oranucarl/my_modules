from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_expatriate_tag(self):
        """Get the employee tag marked as expatriate"""
        return self.env['hr.employee.category'].search(
            [('is_expatriate', '=', True)], limit=1
        )

    @api.onchange('category_ids')
    def _onchange_category_ids_expatriate(self):
        """When expatriate tag is added/removed, sync is_non_resident"""
        expat_tag = self._get_expatriate_tag()
        if not expat_tag:
            return

        # If expatriate tag is present and is_non_resident is False, set it True
        if expat_tag in self.category_ids and not self.is_non_resident:
            self.is_non_resident = True
        # If expatriate tag is absent and is_non_resident is True, set it False
        elif expat_tag not in self.category_ids and self.is_non_resident:
            self.is_non_resident = False

    @api.onchange('is_non_resident')
    def _onchange_is_non_resident_expatriate(self):
        """When is_non_resident changes, sync expatriate tag"""
        expat_tag = self._get_expatriate_tag()
        if not expat_tag:
            return

        # If is_non_resident is True and tag not present, add it
        if self.is_non_resident and expat_tag not in self.category_ids:
            self.category_ids = [(4, expat_tag.id)]
        # If is_non_resident is False and tag is present, remove it
        elif not self.is_non_resident and expat_tag in self.category_ids:
            self.category_ids = [(3, expat_tag.id)]

    def write(self, vals):
        """Override write to sync expatriate tag and is_non_resident on backend changes"""
        result = super().write(vals)

        # Skip sync if context flag is set to prevent infinite loops
        if self.env.context.get('skip_expat_sync'):
            return result

        expat_tag = self._get_expatriate_tag()
        if not expat_tag:
            return result

        # Handle category_ids changes
        if 'category_ids' in vals:
            for employee in self:
                has_expat_tag = expat_tag in employee.category_ids
                # If tag added and is_non_resident is False, set it True
                if has_expat_tag and not employee.is_non_resident:
                    employee.with_context(skip_expat_sync=True).write({
                        'is_non_resident': True
                    })
                # If tag removed and is_non_resident is True, set it False
                elif not has_expat_tag and employee.is_non_resident:
                    employee.with_context(skip_expat_sync=True).write({
                        'is_non_resident': False
                    })

        # Handle is_non_resident changes
        if 'is_non_resident' in vals:
            for employee in self:
                has_expat_tag = expat_tag in employee.category_ids
                # If is_non_resident set to True and tag absent, add it
                if employee.is_non_resident and not has_expat_tag:
                    employee.with_context(skip_expat_sync=True).write({
                        'category_ids': [(4, expat_tag.id)]
                    })
                # If is_non_resident set to False and tag present, remove it
                elif not employee.is_non_resident and has_expat_tag:
                    employee.with_context(skip_expat_sync=True).write({
                        'category_ids': [(3, expat_tag.id)]
                    })

        return result
