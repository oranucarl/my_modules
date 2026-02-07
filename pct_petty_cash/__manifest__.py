# -*- coding: utf-8 -*-
{
    'name': 'Petty Cash Management',
    'version': '18.0.1.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Manage petty cash custodians, allocations and expenses',
    'description': """
Petty Cash Management
=====================

This module allows users to manage petty cash operations:

* Create petty cash records for custodians
* Track amount allocations from company bank accounts
* Record expenses made by custodians
* Generate journal entries for allocations and expenses
* Support analytic distribution for cost tracking

Features:
---------
* Custodian-based petty cash management
* Automatic journal entry creation
* Year-to-date tracking of allocations and expenses
* Previous year balance brought forward
* Three-level security: Users, Accountants, Managers
* Wizards for easy data entry by custodians
    """,
    'author': 'PCT',
    'website': 'https://www.packetclouds.com',
    'depends': [
        'account',
        'analytic',
    ],
    'data': [
        'security/pct_petty_cash_security.xml',
        'security/ir.model.access.csv',
        'wizards/allocation_wizard_views.xml',
        'wizards/expense_wizard_views.xml',
        'wizards/cash_report_wizard_views.xml',
        'views/pct_petty_cash_views.xml',
        'views/res_config_settings_views.xml',
        'views/pct_petty_cash_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
