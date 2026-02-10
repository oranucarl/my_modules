{
    'name': 'Delete Access Control',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Restrict delete access for all users unless granted special permission',
    'description': """
        This module restricts the ability to delete records for all users.
        Only users with the 'Delete Records' access right can delete records.
    """,
    'author': 'PCT',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/security.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
