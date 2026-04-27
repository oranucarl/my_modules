from odoo import fields, models


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    sample_type_id = fields.Many2one(
        'quality.sample.type',
        string='Sample Type',
        related='point_id.sample_type_id',
        readonly=True,
        store=True,
    )
    sample_id = fields.Many2one(
        'quality.sample',
        string='Sample',
        related='point_id.sample_id',
        readonly=True,
        store=True,
    )
