from odoo import fields, models


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    sample_type_id = fields.Many2one(
        'quality.sample.type',
        string='Sample Type',
    )
    sample_id = fields.Many2one(
        'quality.sample',
        string='Sample',
    )
