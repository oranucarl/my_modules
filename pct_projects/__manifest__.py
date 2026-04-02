# -*- coding: utf-8 -*-
{
    'name': 'Project Configuration',
    'version': '18.0.1.0.0',
    'summary': 'Adds project configuration and analytic distribution support to Purchases, Bills, and Payments.',
    'description': """
        This module introduces a new Project Configuration model that links Odoo Projects
        with analytic distributions and prefixes. It also integrates project tracking into
        Purchase Orders, Vendor Bills, and Payments.
    """,
    'category': 'Accounting & Purchase',
    'author': "Packetclouds Technology",
    'website': "https://www.packetclouds.com",
    'license': 'LGPL-3',
    'depends': ['base', 'project', 'purchase', 'account', 'analytic', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/project_security.xml',
        'views/project_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/report_invoice.xml',
    ],
    'installable': True,
    'application': False,
}
