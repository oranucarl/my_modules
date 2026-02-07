{
    'name': 'PCT Addon',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Adds serial number, assigned employee and department fields to assets',
    'description': """
PCT Asset Addon
===============
This module extends the account.asset model with the following fields:
- Serial Number: A character field to store the asset's serial number
- Assigned To: An employee field to track who the asset is assigned to
- Department: A related field showing the department of the assigned employee
    """,
    'author': 'PCT',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'account_asset',
        'hr',
    ],
    'data': [
        'views/account_asset_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
