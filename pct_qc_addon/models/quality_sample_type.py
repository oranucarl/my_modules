from odoo import fields, models


class QualitySampleType(models.Model):
    _name = 'quality.sample.type'
    _description = 'Quality Sample Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
