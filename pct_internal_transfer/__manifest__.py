# -*- coding: utf-8 -*-
{
    'name': 'Internal Bank Transfer',
    'version': '18.0.1.0.0',
    'summary': 'Adds Internal Transfer as a payment type for inter-bank transfers',
    'description': """
        This module extends the Payment model to add a third payment type option
        for internal bank transfers. When selected, a destination journal field
        appears, and posting the payment creates proper journal entries to
        credit the source bank and debit the destination bank.
    """,
    'category': 'Accounting/Payment',
    'author': "Carlson Oranu",
    'website': "https://www.packetclouds.com",
    'license': 'LGPL-3',
    'depends': ['account', 'hr_expense'],
    'data': [
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'application': False,
}
