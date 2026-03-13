{
    'name': 'PCT Expatriate Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Comprehensive expatriate employee management — housing, allowances, documents, and payroll',
    'description': """
        Standalone expatriate management application.
        - Expatriate employee tracking via employee tags
        - Two-way sync between expatriate tag and non-resident status
        - Monthly allowance tracking with Year/Month grouping
        - Housing management with lease renewal alerts
        - Residence permit and CERPEC document tracking with expiry alerts
        - Sponsor company master data
        - Replica payroll menus (contracts, payslips, batches) filtered to expatriate data
        - Daily cron for expiry recalculation
        - Restricted to Expatriate Payroll Manager access group only
    """,
    'author': 'PCT',
    'depends': [
        'pct_payroll_expatriate',
        'hr',
        'hr_contract',
        'hr_payroll',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/default_data.xml',
        'data/cron.xml',
        'views/hr_employee_category_views.xml',
        'views/expatriate_sponsor_company_views.xml',
        'views/expatriate_allowance_views.xml',
        'views/expatriate_housing_views.xml',
        'views/expatriate_document_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
