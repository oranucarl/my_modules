# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    shift = fields.Selection(
        selection=[
            ('shift_a_day', 'Shift A – Day'),
            ('shift_a_night', 'Shift A – Night'),
            ('shift_b_day', 'Shift B – Day'),
            ('shift_b_night', 'Shift B – Night'),
            ('shift_c_day', 'Shift C – Day'),
            ('shift_c_night', 'Shift C – Night'),
        ],
        string='Shift',
    )
