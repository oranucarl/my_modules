from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    driver_name = fields.Char(string="Driver Name")
    truck_number = fields.Char(string="Truck Number")
