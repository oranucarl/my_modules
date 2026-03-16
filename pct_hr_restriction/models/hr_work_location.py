# -*- coding: utf-8 -*-

from odoo import fields, models


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    site_hr_officer_ids = fields.Many2many(
        comodel_name='res.users',
        relation='hr_work_location_hr_officer_rel',
        column1='work_location_id',
        column2='user_id',
        string='Site HR Officers',
        help='Users assigned as HR Officers for this work location. '
             'These users will have full HR access to employees at this location. '
             'Only users who work at this location can be assigned.',
    )
