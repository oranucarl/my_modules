{
    'name': 'PCT Expatriate Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Comprehensive expatriate employee management — housing, allowances, documents, and payroll',
    'description': """
        Comprehensive expatriate management application.

        Features:
        - Expatriate employee tracking via employee tags
        - Two-way sync between expatriate tag and non-resident status
        - Monthly allowance tracking with Year/Month grouping
        - Housing management with lease renewal alerts
        - Residence permit and CERPEC document tracking with expiry alerts
        - Sponsor company master data
        - Segregated payroll management (contracts, payslips, batches)
        - Daily cron for expiry recalculation
        - Restricted to Expatriate Payroll Manager access group
    """,
    'author': 'Carlson Oranu',
    'website': 'https://www.packetclouds.com',
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_payroll',
        'mail',
        'product',
        'fleet',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/default_data.xml',
        'data/email_template.xml',
        'data/cron.xml',
        'views/hr_payroll_structure_type_views.xml',
        'views/hr_payslip_employees_views.xml',
        'views/hr_employee_category_views.xml',
        'views/hr_contract_views.xml',
        'views/expatriate_sponsor_company_views.xml',
        'views/expatriate_document_type_views.xml',
        'views/expatriate_allowance_views.xml',
        'views/housing_cost_line_views.xml',
        'views/expatriate_housing_views.xml',
        'wizard/housing_export_wizard_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
}
