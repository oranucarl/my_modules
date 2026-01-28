# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    branch_id = fields.Many2one(
        'res.branch',
        related='warehouse_id.branch_id',
        string='Branch'
    )   