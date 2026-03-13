from odoo import api, fields, models


class HousingCostLine(models.Model):
    _name = 'housing.cost.line'
    _description = 'Housing Cost Line'

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
        default=fields.Date.today
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
