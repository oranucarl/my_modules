# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# Store original domains for record rules that we modify
# Format: {'xml_id': 'original_domain'}
# Currently we only ADD new rules, we don't modify existing ones.
# If in the future we need to modify base rules, store originals here.
ORIGINAL_RULE_DOMAINS = {
    # Example (if we were modifying existing rules):
    # 'hr.hr_employee_rule': "[(1, '=', 1)]",
}


def uninstall_hook(env):
    """
    Clean up when the module is uninstalled.

    This hook ensures that:
    1. Any modifications to base module record rules are restored to original values
    2. Custom record rules created by this module are automatically removed by Odoo
       (via XML ID deletion)

    Note: The Many2Many relation data for site_hr_officer_ids is intentionally
    preserved so that if the module is reinstalled, the existing configuration
    is retained.
    """
    _logger.info("PCT HR Restriction: Running uninstall hook...")

    # Restore any modified base record rules to their original domains
    for xml_id, original_domain in ORIGINAL_RULE_DOMAINS.items():
        try:
            rule = env.ref(xml_id, raise_if_not_found=False)
            if rule:
                rule.write({
                    'domain_force': original_domain,
                })
                _logger.info(
                    "PCT HR Restriction: Restored original domain for %s", xml_id
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
    # - pct_hr_restriction.hr_employee_public_own_record_rule
    # - pct_hr_restriction.hr_employee_public_hr_officer_rule
    # - pct_hr_restriction.hr_employee_public_hr_manager_rule
    # - pct_hr_restriction.hr_employee_hr_manager_full_access_rule
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
