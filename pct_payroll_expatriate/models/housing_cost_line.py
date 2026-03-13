from odoo import api, fields, models


class HousingCostLine(models.Model):
    _name = 'housing.cost.line'
    _description = 'Housing Cost Line'
    _order = 'date desc, id desc'

    housing_id = fields.Many2one(
        'expatriate.housing',
        string='Housing',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Description',
        required=True
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today
    )
    amount = fields.Monetary(
        string='Amount',
        required=True
    )
    currency_id = fields.Many2one(
        related='housing_id.currency_id',
        store=True,
        readonly=True
    )
