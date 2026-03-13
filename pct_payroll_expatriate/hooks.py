from odoo import api, SUPERUSER_ID


def post_uninstall_hook(env):
    """Restore original menu actions when module is uninstalled"""

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
        menu_payroll_contracts = env.ref('hr_payroll.menu_hr_payroll_employees_root', raise_if_not_found=False)
        action_contracts = env.ref('hr_contract.action_hr_contract', raise_if_not_found=False)
        if menu_payroll_contracts and action_contracts:
            menu_payroll_contracts.action = 'ir.actions.act_window,%s' % action_contracts.id
    except Exception as e:
        pass
