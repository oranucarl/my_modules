{
    'name': 'PCT Fleet',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Fleet and Asset Management Integration',
    'description': """
        Fleet management enhancements and asset integration.

        Features:
        - Sync vehicle values with linked assets
        - When a vehicle is linked to an asset, original_value syncs to net_car_value
        - When book_value changes on asset, it syncs to residual_value on vehicle
    """,
    'author': 'Carlson Oranu',
    'website': 'https://www.packetclouds.com',
    'depends': [
        'fleet',
        'account_asset',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
