{
    'name': 'Employee Work Location History',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Track and report employee work location assignment history',
    'description': """
        This module tracks the history of employee work location assignments.

        Features:
        - Automatic tracking of work location changes
        - Records who made the change and when
        - View work location history from employee form
        - Reporting with list, graph, and pivot views
        - Filter by employee, work location, period, and user
    """,
    'author': 'Carlson Oranu',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/work_location_history_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
