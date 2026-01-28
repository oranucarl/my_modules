# -*- coding: utf-8 -*-
{
    'name': 'Branch Management',
    'version': '18.0.1.0.0',
    'summary': 'Adds branch management and branch linkage to core business models',
    'description': """
        This module introduces a new Branch model (`res.branch`) for managing organizational branches
        and integrates branch selection into key business documents such as Sales Orders,
        Purchase Orders, Invoices, Payments, and Stock Pickings.

        Features:
        - Branch User and Branch Manager security groups
        - Record-level security rules for branch isolation
        - Multi-branch switching support
        - Branch fields on users, sales, purchases, inventory, accounting, HR, POS, and manufacturing
    """,
    'category': 'Sales/Configuration',
    'author': "Carlson Oranu",
    'website': "https://www.packetclouds.com",
    'license': 'LGPL-3',
    'depends': [
        # Core
        'base',
        'mail',
        'analytic',
        # Sales & CRM
        'sale_management',
        'sales_team',
        # Purchase
        'purchase',
        # Inventory
        'stock',
        # Accounting
        'account',
        # Products
        'product',
        # HR (Community)
        'hr',
        'hr_contract',
        # HR (Enterprise)
        'hr_payroll',
        # POS
        'point_of_sale',
        # Manufacturing
        'mrp',
        # Approvals (Enterprise)
        'approvals',
    ],
    'data': [
        # Security (must be loaded first)
        'security/pct_branch_security.xml',
        'security/ir.model.access.csv',
        # Core views
        'views/branch_views.xml',
        'views/res_users_views.xml',
        'views/partner_views.xml',
        # 'views/product_views.xml',
        # Sales & CRM
        'views/sale_views.xml',
        'views/crm_views.xml',
        # Purchase
        'views/purchase_views.xml',
        # Inventory
        'views/stock_views.xml',
        # Accounting
        'views/account_views.xml',
        # HR (Community)
        'views/hr_views.xml',
        # HR (Enterprise)
        'views/hr_payroll_views.xml',
        # POS
        'views/pos_views.xml',
        # Manufacturing
        'views/mrp_views.xml',
        # Approvals (Enterprise)
        'views/approval_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
