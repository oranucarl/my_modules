# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state_of_origin = fields.Many2one(
        'res.country.state',
        string='State of Origin',
        domain="[('country_id', '=?', country_id)]",
        groups="hr.group_hr_user",
        tracking=True,
    )

    @api.onchange('country_id')
    def _onchange_country_id_state_of_origin(self):
        """Clear state_of_origin when country changes"""
        if self.state_of_origin and self.state_of_origin.country_id != self.country_id:
            self.state_of_origin = False
