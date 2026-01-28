# -*- coding: utf-8 -*-
from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        domain="[('company_id', '=', company_id)]"
    )

    bank_information = fields.Html(
        string="Bank Information",
        help="Optional bank/payment details for this warehouse."
    )
