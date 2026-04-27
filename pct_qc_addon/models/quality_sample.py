from odoo import fields, models


class QualitySample(models.Model):
    _name = 'quality.sample'
    _description = 'Quality Sample'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
