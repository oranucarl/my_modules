# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# Store original values for actions that we modify
ORIGINAL_ACTIONS = {
    'hr.hr_employee_public_action': {
        'domain': "[('company_id', 'in', allowed_company_ids)]",
        'help': """<p class="o_view_nocontent_smiling_face">
                Add a new employee
            </p>
            <p>
                Quickly find all the information you need for your employees such as contact data, job position, availability, etc.
            </p>""",
    },
}

# Store original values for record rules that we override
# These rules originally had NO groups (applied to all users)
ORIGINAL_RULES = {
    'hr.hr_dept_comp_rule': {
        'groups': [],  # Empty = applies to all users
        'domain_force': "[('company_id', 'in', company_ids + [False])]",
        'perm_read': True,
        'perm_write': True,
        'perm_create': True,
        'perm_unlink': True,
    },
    'hr.hr_job_comp_rule': {
        'groups': [],
        'domain_force': "[('company_id', 'in', company_ids + [False])]",
        'perm_read': True,
        'perm_write': True,
        'perm_create': True,
        'perm_unlink': True,
    },
    'hr.ir_rule_hr_contract_type_multi_company': {
        'groups': [],
        'domain_force': "['|', ('country_id', '=', False), ('country_id', 'in', user.env.companies.country_id.ids)]",
        'perm_read': True,
        'perm_write': True,
        'perm_create': True,
        'perm_unlink': True,
    },
}


def uninstall_hook(env):
    """
    Clean up when the module is uninstalled.

    This hook ensures that:
    1. Modified window actions are restored to their original values
    2. Overridden base record rules are restored to their original state
    3. Custom record rules created by this module are automatically removed by Odoo
       (via XML ID deletion)

    Note: The Many2Many relation data for site_hr_officer_ids is intentionally
    preserved so that if the module is reinstalled, the existing configuration
    is retained.
    """
    _logger.info("PCT HR Restriction: Running uninstall hook...")

    # Restore modified window actions to their original values
    for xml_id, original_values in ORIGINAL_ACTIONS.items():
        try:
            action = env.ref(xml_id, raise_if_not_found=False)
            if action:
                action.write({
                    'domain': original_values.get('domain', '[]'),
                    'help': original_values.get('help', ''),
                })
                _logger.info(
                    "PCT HR Restriction: Restored original values for action %s", xml_id
                )
        except Exception as e:
            _logger.warning(
                "PCT HR Restriction: Could not restore action %s: %s", xml_id, e
            )

    # Restore overridden base record rules to their original state
    for xml_id, original_values in ORIGINAL_RULES.items():
        try:
            rule = env.ref(xml_id, raise_if_not_found=False)
            if rule:
                # Clear groups (set to empty = applies to all users)
                rule.write({
                    'groups': [(5, 0, 0)],  # Clear all groups
                    'domain_force': original_values.get('domain_force'),
                    'perm_read': original_values.get('perm_read', True),
                    'perm_write': original_values.get('perm_write', True),
                    'perm_create': original_values.get('perm_create', True),
                    'perm_unlink': original_values.get('perm_unlink', True),
                })
                _logger.info(
                    "PCT HR Restriction: Restored original values for rule %s", xml_id
                )
        except Exception as e:
            _logger.warning(
                "PCT HR Restriction: Could not restore rule %s: %s", xml_id, e
            )

    # The custom rules we created will be automatically removed when the module
    # is uninstalled because they have XML IDs tied to this module.
    #
    # Rules that will be auto-removed:
    # - pct_hr_restriction.hr_employee_hr_officer_location_rule
    # - pct_hr_restriction.hr_employee_public_hr_officer_rule
    # - pct_hr_restriction.hr_employee_public_hr_manager_rule
    # - pct_hr_restriction.hr_employee_hr_manager_full_access_rule
    # - pct_hr_restriction.hr_work_location_hr_officer_rule
    # - pct_hr_restriction.hr_work_location_hr_manager_rule
    # - pct_hr_restriction.hr_department_hr_user_readonly_rule
    # - pct_hr_restriction.hr_employee_category_hr_user_readonly_rule
    # - pct_hr_restriction.hr_job_hr_user_readonly_rule
    # - pct_hr_restriction.hr_contract_type_hr_user_readonly_rule
    # - pct_hr_restriction.resource_calendar_hr_user_readonly_rule
    # - pct_hr_restriction.resource_calendar_attendance_hr_user_readonly_rule

    # Note: We intentionally DO NOT clear the Many2Many relation data
    # (hr_work_location_hr_officer_rel table) so that if the module is
    # reinstalled, the Site HR Officer assignments are preserved.

    # Invalidate cache to ensure clean state
    env.registry.clear_cache()

    _logger.info("PCT HR Restriction: Uninstall hook completed successfully")
