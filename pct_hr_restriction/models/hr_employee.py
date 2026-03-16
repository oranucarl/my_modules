# -*- coding: utf-8 -*-
"""
HR Employee Model Extensions for PCT HR Restriction

Design Decision: work_location_id is NOT made required
-------------------------------------------------------
Originally considered making work_location_id required on hr.employee,
but this was intentionally not implemented because:

1. Employees without a work location should simply not be accessible
   to Site HR Officers - they can only be managed by HR Managers.

2. This allows flexibility for:
   - New employees not yet assigned to a location
   - Employees in transition between locations
   - Central/HQ employees who may not have a specific work location

3. The record rules handle this correctly:
   - HR Managers: Full access to ALL employees (with or without location)
   - Site HR Officers: Access only to employees AT their assigned locations
   - Employees without location: Only accessible by HR Managers

This file is kept as documentation. No model changes are required.
"""
