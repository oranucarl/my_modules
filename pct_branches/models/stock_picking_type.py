# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        related='warehouse_id.branch_id'
    )
