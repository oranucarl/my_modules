from odoo import fields, models


class FleetVehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    cost_frequency = fields.Selection(
        selection_add=[
            ('bi_annual', 'Bi-Annual'),
        ],
        ondelete={
            'bi_annual': 'set default',
        }
    )
