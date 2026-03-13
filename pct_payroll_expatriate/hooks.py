from odoo import api, SUPERUSER_ID


def uninstall_hook(env):
    """Restore original menu actions and record rules when module is uninstalled"""

    # =============================================
    # RESTORE ORIGINAL RECORD RULES
    # =============================================

    # Restore hr_contract.ir_rule_hr_contract_manager - original: [(1, '=', 1)]
    try:
        rule = env.ref('hr_contract.ir_rule_hr_contract_manager', raise_if_not_found=False)
        if rule:
            rule.domain_force = "[(1, '=', 1)]"
    except Exception:
        pass

    # Restore hr_contract.ir_rule_hr_contract_employee_manager - original domain
    try:
        rule = env.ref('hr_contract.ir_rule_hr_contract_employee_manager', raise_if_not_found=False)
        if rule:
            rule.domain_force = "['|', ('employee_id.parent_id.user_id', '=', user.id), ('employee_id.user_id', '=', user.id)]"
    except Exception:
        pass

    # Restore hr_payroll.hr_payslip_rule_manager - original: [(1, '=', 1)]
    try:
        rule = env.ref('hr_payroll.hr_payslip_rule_manager', raise_if_not_found=False)
        if rule:
            rule.domain_force = "[(1, '=', 1)]"
    except Exception:
        pass

    # Restore hr_payroll.hr_payroll_rule_officer - original domain
    try:
        rule = env.ref('hr_payroll.hr_payroll_rule_officer', raise_if_not_found=False)
        if rule:
            rule.domain_force = "['|', '|', ('employee_id.user_id', '=', user.id), ('employee_id.department_id', '=', False), ('employee_id.department_id.manager_id.user_id', '=', user.id)]"
    except Exception:
        pass

    # =============================================
    # RESTORE ORIGINAL MENU ACTIONS
    # =============================================

    # Restore Payroll → Payslips → Batches menu
    try:
        menu_batches = env.ref('hr_payroll.menu_hr_payslip_run', raise_if_not_found=False)
        action_batches = env.ref('hr_payroll.action_hr_payslip_run_tree', raise_if_not_found=False)
        if menu_batches and action_batches:
            menu_batches.action = 'ir.actions.act_window,%s' % action_batches.id
    except Exception as e:
        pass  # Silently continue if menu/action doesn't exist

    # Restore Payroll → Payslips → All Payslips menu
    try:
        menu_payslips = env.ref('hr_payroll.menu_hr_payroll_employee_payslips', raise_if_not_found=False)
        action_payslips = env.ref('hr_payroll.action_view_hr_payslip_month_form', raise_if_not_found=False)
        if menu_payslips and action_payslips:
            menu_payslips.action = 'ir.actions.act_window,%s' % action_payslips.id
    except Exception as e:
        pass

    # Restore Employees → Employees → Contracts menu
    try:
        menu_emp_contracts = env.ref('hr_contract.hr_menu_contract', raise_if_not_found=False)
        action_contracts = env.ref('hr_contract.action_hr_contract', raise_if_not_found=False)
        if menu_emp_contracts and action_contracts:
            menu_emp_contracts.action = 'ir.actions.act_window,%s' % action_contracts.id
    except Exception as e:
        pass

    # Restore Payroll → Contracts menu
    try:
        menu_payroll_contracts = env.ref('hr_payroll.hr_menu_all_contracts', raise_if_not_found=False)
        action_contracts = env.ref('hr_contract.action_hr_contract', raise_if_not_found=False)
        if menu_payroll_contracts and action_contracts:
            menu_payroll_contracts.action = 'ir.actions.act_window,%s' % action_contracts.id
    except Exception as e:
        pass
