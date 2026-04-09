from odoo import fields, models


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(
        selection_add=[
            ('lorry', 'Lorry'),
            ('truck', 'Truck'),
            ('truck_lorry', 'Truck/Lorry'),
            ('truck_hiab', 'Truck/Hiab'),
            ('motorcycle', 'Motorcycles'),
            ('suv', 'SUV'),
            ('mini_bus', 'Mini Bus'),
            ('saloon', 'Saloon'),
            ('pick_up', 'Pick Up'),
            ('saloon_sedan', 'Saloon/Sedan'),
            ('bus', 'Bus'),
            ('light_vehicle', 'Light Vehicles'),
        ],
        ondelete={
            'lorry': 'set default',
            'truck': 'set default',
            'truck_lorry': 'set default',
            'truck_hiab': 'set default',
            'motorcycle': 'set default',
            'suv': 'set default',
            'mini_bus': 'set default',
            'saloon': 'set default',
            'pick_up': 'set default',
            'saloon_sedan': 'set default',
            'bus': 'set default',
            'light_vehicle': 'set default',
        }
    )
