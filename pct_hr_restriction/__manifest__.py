# -*- coding: utf-8 -*-
{
    'name': 'PCT HR Restriction',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Location-based HR access restrictions',
    'description': """
PCT HR Restriction
==================

This module implements location-based access control for HR users:

Features:
---------
* Adds Site HR Officer field to Work Location (Many2Many to users)
* Makes work_location_id required on hr.employee
* HR Managers retain full access to all employee records
* HR Officers (hr.group_hr_user):
    - If assigned to work locations: Full access to employees at those locations
    - If not assigned to any location: Access only to their own employee record
* HR Officers get read-only access to:
    - Departments
    - Employee Categories
    - Job Positions
    - Contract Types (Employment Types)
    - Working Schedules (Resource Calendars)
* Regular users: Menu-level restriction (not record rules) to preserve
    related field selections in Expenses, Timesheets, etc.

Uninstall Hook:
---------------
When uninstalled, all modified record rules are reset to their original values.
    """,
    'author': 'Carlson Oranu',
    'website': 'https://www.packetclouds.com',
    'depends': [
        'base',
        'hr',
        'resource',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_work_location_views.xml',
        'views/hr_employee_public_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
}
