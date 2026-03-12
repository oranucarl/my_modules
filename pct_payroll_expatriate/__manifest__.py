{
    'name': 'PCT Payroll Expatriate',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Segregated payroll management for expatriate staff',
    'description': """
        This module provides segregated payroll management for expatriate employees.

        Features:
        - Separate menus for expatriate payslips, batches, and contracts
        - Record rules to restrict access based on expatriate status
        - Expatriate identification via salary structure type
        - Security group for expatriate payroll managers
    """,
    'author': 'Carlson Oranu',
    'depends': [
        'hr_payroll',
        'hr_contract',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll_structure_type_views.xml',
        'views/hr_payslip_employees_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
