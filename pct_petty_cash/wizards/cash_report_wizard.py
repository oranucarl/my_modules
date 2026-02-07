# -*- coding: utf-8 -*-

import io
import base64
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class PctCashReportWizard(models.TransientModel):
    _name = 'pct.cash.report.wizard'
    _description = 'Cash Report Wizard'

    custodian_id = fields.Many2one(
        'res.users',
        string='Custodian',
        help='Filter by custodian. Leave empty to show all.',
    )
    year = fields.Selection(
        selection='_get_year_selection',
        string='Year',
        help='Filter by year. Leave empty to show all years.',
    )

    # Lines for display and selection
    allocation_line_ids = fields.Many2many(
        'pct.petty.cash.allocation',
        'pct_cash_report_wizard_allocation_rel',
        'wizard_id',
        'allocation_id',
        string='Allocations',
    )
    expense_line_ids = fields.Many2many(
        'pct.petty.cash.expense',
        'pct_cash_report_wizard_expense_rel',
        'wizard_id',
        'expense_id',
        string='Expenses',
    )

    # Summary fields
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    amount_brought_forward = fields.Monetary(
        string='Rollover from Previous Year',
        currency_field='currency_id',
        compute='_compute_summary',
    )
    total_allocated = fields.Monetary(
        string='Total Allocated',
        currency_field='currency_id',
        compute='_compute_summary',
    )
    total_expensed = fields.Monetary(
        string='Total Expensed',
        currency_field='currency_id',
        compute='_compute_summary',
    )
    balance = fields.Monetary(
        string='Balance',
        currency_field='currency_id',
        compute='_compute_summary',
    )

    @api.model
    def _get_year_selection(self):
        """Generate year selection based on years with actual records"""
        years = set()

        # Get years from allocations
        self.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM payment_date)::INTEGER as year
            FROM pct_petty_cash_allocation
            WHERE payment_date IS NOT NULL
        """)
        for row in self.env.cr.fetchall():
            if row[0]:
                years.add(row[0])

        # Get years from expenses
        self.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM expense_date)::INTEGER as year
            FROM pct_petty_cash_expense
            WHERE expense_date IS NOT NULL
        """)
        for row in self.env.cr.fetchall():
            if row[0]:
                years.add(row[0])

        # Always include current year even if no records yet
        years.add(date.today().year)

        # Sort and return as selection
        return [(str(year), str(year)) for year in sorted(years)]

    def _get_allocation_domain(self):
        """Build domain for allocations based on filters"""
        domain = []
        if self.custodian_id:
            domain.append(('petty_cash_id.custodian_id', '=', self.custodian_id.id))
        if self.year:
            year_int = int(self.year)
            domain.append(('payment_date', '>=', date(year_int, 1, 1)))
            domain.append(('payment_date', '<=', date(year_int, 12, 31)))
        # Apply user access restriction for regular users
        if not self.env.user.has_group('pct_petty_cash.group_petty_cash_accountant'):
            domain.append(('petty_cash_id.custodian_id', '=', self.env.user.id))
        return domain

    def _get_expense_domain(self):
        """Build domain for expenses based on filters"""
        domain = []
        if self.custodian_id:
            domain.append(('petty_cash_id.custodian_id', '=', self.custodian_id.id))
        if self.year:
            year_int = int(self.year)
            domain.append(('expense_date', '>=', date(year_int, 1, 1)))
            domain.append(('expense_date', '<=', date(year_int, 12, 31)))
        # Apply user access restriction for regular users
        if not self.env.user.has_group('pct_petty_cash.group_petty_cash_accountant'):
            domain.append(('petty_cash_id.custodian_id', '=', self.env.user.id))
        return domain

    @api.depends('allocation_line_ids', 'expense_line_ids', 'custodian_id', 'year')
    def _compute_summary(self):
        """Compute summary totals"""
        for wizard in self:
            # Calculate totals from current lines
            wizard.total_allocated = sum(wizard.allocation_line_ids.mapped('amount'))
            wizard.total_expensed = sum(wizard.expense_line_ids.mapped('amount'))

            # Calculate amount brought forward (from petty cash records)
            amount_brought_forward = 0.0
            if wizard.custodian_id:
                # Get petty cash records for this custodian
                petty_cash_records = self.env['pct.petty.cash'].search([
                    ('custodian_id', '=', wizard.custodian_id.id)
                ])
                amount_brought_forward = sum(petty_cash_records.mapped('amount_brought_forward'))
            else:
                # Get all petty cash records (respecting user access)
                domain = []
                if not self.env.user.has_group('pct_petty_cash.group_petty_cash_accountant'):
                    domain.append(('custodian_id', '=', self.env.user.id))
                petty_cash_records = self.env['pct.petty.cash'].search(domain)
                amount_brought_forward = sum(petty_cash_records.mapped('amount_brought_forward'))

            wizard.amount_brought_forward = amount_brought_forward
            wizard.balance = amount_brought_forward + wizard.total_allocated - wizard.total_expensed

    @api.model
    def default_get(self, fields_list):
        """Set default values and load initial data"""
        res = super().default_get(fields_list)

        # If user is only a petty cash user (not accountant/manager), default to themselves
        if not self.env.user.has_group('pct_petty_cash.group_petty_cash_accountant'):
            res['custodian_id'] = self.env.user.id

        # Load initial data
        allocation_domain = []
        expense_domain = []

        # Apply user access restriction for regular users
        if not self.env.user.has_group('pct_petty_cash.group_petty_cash_accountant'):
            allocation_domain.append(('petty_cash_id.custodian_id', '=', self.env.user.id))
            expense_domain.append(('petty_cash_id.custodian_id', '=', self.env.user.id))

        allocations = self.env['pct.petty.cash.allocation'].search(allocation_domain)
        expenses = self.env['pct.petty.cash.expense'].search(expense_domain)

        res['allocation_line_ids'] = [(6, 0, allocations.ids)]
        res['expense_line_ids'] = [(6, 0, expenses.ids)]

        return res

    @api.onchange('custodian_id', 'year')
    def _onchange_filters(self):
        """Update lines when filters change"""
        allocation_domain = self._get_allocation_domain()
        expense_domain = self._get_expense_domain()

        self.allocation_line_ids = self.env['pct.petty.cash.allocation'].search(allocation_domain)
        self.expense_line_ids = self.env['pct.petty.cash.expense'].search(expense_domain)

    def action_export_excel(self):
        """Export report to Excel"""
        self.ensure_one()

        if not xlsxwriter:
            raise UserError(_('xlsxwriter library is not installed. Please install it to export Excel files.'))

        # Use the lines that are currently in the wizard (user may have deselected some)
        allocations = self.allocation_line_ids
        expenses = self.expense_line_ids

        if not allocations and not expenses:
            raise UserError(_('No records to export. Please adjust your filters.'))

        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })
        money_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })
        date_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd',
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
        })

        # Report title info
        title = 'Petty Cash Report'
        if self.custodian_id:
            title += f' - {self.custodian_id.name}'
        if self.year:
            title += f' ({self.year})'

        # Allocations Sheet
        alloc_sheet = workbook.add_worksheet('Allocations')
        alloc_sheet.merge_range('A1:G1', title, title_format)
        alloc_sheet.set_row(0, 25)

        # Allocations headers
        alloc_headers = ['Date', 'Petty Cash', 'Custodian', 'Amount', 'Source Journal', 'Status', 'Journal Entry']
        for col, header in enumerate(alloc_headers):
            alloc_sheet.write(2, col, header, header_format)

        # Allocations data
        row = 3
        total_allocated = 0
        for alloc in allocations:
            alloc_sheet.write(row, 0, alloc.payment_date.strftime('%Y-%m-%d') if alloc.payment_date else '', date_format)
            alloc_sheet.write(row, 1, alloc.petty_cash_id.name or '', cell_format)
            alloc_sheet.write(row, 2, alloc.petty_cash_id.custodian_id.name or '', cell_format)
            alloc_sheet.write(row, 3, alloc.amount or 0, money_format)
            alloc_sheet.write(row, 4, alloc.source_journal_id.name or '', cell_format)
            alloc_sheet.write(row, 5, dict(alloc._fields['state'].selection).get(alloc.state, ''), cell_format)
            alloc_sheet.write(row, 6, alloc.move_id.name or '', cell_format)
            total_allocated += alloc.amount or 0
            row += 1

        # Total row
        alloc_sheet.write(row, 2, 'Total:', header_format)
        alloc_sheet.write(row, 3, total_allocated, money_format)

        # Set column widths
        alloc_sheet.set_column('A:A', 12)
        alloc_sheet.set_column('B:B', 20)
        alloc_sheet.set_column('C:C', 20)
        alloc_sheet.set_column('D:D', 15)
        alloc_sheet.set_column('E:E', 20)
        alloc_sheet.set_column('F:F', 10)
        alloc_sheet.set_column('G:G', 15)

        # Expenses Sheet
        exp_sheet = workbook.add_worksheet('Expenses')
        exp_sheet.merge_range('A1:H1', title, title_format)
        exp_sheet.set_row(0, 25)

        # Expenses headers
        exp_headers = ['Date', 'Petty Cash', 'Custodian', 'Description', 'Category', 'Amount', 'Status', 'Journal Entry']
        for col, header in enumerate(exp_headers):
            exp_sheet.write(2, col, header, header_format)

        # Expenses data
        row = 3
        total_expensed = 0
        for exp in expenses:
            exp_sheet.write(row, 0, exp.expense_date.strftime('%Y-%m-%d') if exp.expense_date else '', date_format)
            exp_sheet.write(row, 1, exp.petty_cash_id.name or '', cell_format)
            exp_sheet.write(row, 2, exp.petty_cash_id.custodian_id.name or '', cell_format)
            exp_sheet.write(row, 3, exp.description or '', cell_format)
            exp_sheet.write(row, 4, exp.product_id.name or '', cell_format)
            exp_sheet.write(row, 5, exp.amount or 0, money_format)
            exp_sheet.write(row, 6, dict(exp._fields['state'].selection).get(exp.state, ''), cell_format)
            exp_sheet.write(row, 7, exp.move_id.name or '', cell_format)
            total_expensed += exp.amount or 0
            row += 1

        # Total row
        exp_sheet.write(row, 4, 'Total:', header_format)
        exp_sheet.write(row, 5, total_expensed, money_format)

        # Set column widths
        exp_sheet.set_column('A:A', 12)
        exp_sheet.set_column('B:B', 20)
        exp_sheet.set_column('C:C', 20)
        exp_sheet.set_column('D:D', 30)
        exp_sheet.set_column('E:E', 20)
        exp_sheet.set_column('F:F', 15)
        exp_sheet.set_column('G:G', 10)
        exp_sheet.set_column('H:H', 15)

        # Summary Sheet
        summary_sheet = workbook.add_worksheet('Summary')
        summary_sheet.merge_range('A1:C1', title, title_format)
        summary_sheet.set_row(0, 25)

        summary_sheet.write(2, 0, 'Description', header_format)
        summary_sheet.write(2, 1, 'Amount', header_format)

        summary_sheet.write(3, 0, 'Rollover from Previous Year', cell_format)
        summary_sheet.write(3, 1, self.amount_brought_forward, money_format)
        summary_sheet.write(4, 0, 'Total Allocations', cell_format)
        summary_sheet.write(4, 1, total_allocated, money_format)
        summary_sheet.write(5, 0, 'Total Expenses', cell_format)
        summary_sheet.write(5, 1, total_expensed, money_format)
        summary_sheet.write(6, 0, 'Balance', header_format)
        summary_sheet.write(6, 1, self.amount_brought_forward + total_allocated - total_expensed, money_format)

        summary_sheet.set_column('A:A', 30)
        summary_sheet.set_column('B:B', 15)

        workbook.close()
        output.seek(0)

        # Create attachment
        filename = f'petty_cash_report'
        if self.custodian_id:
            filename += f'_{self.custodian_id.name.replace(" ", "_")}'
        if self.year:
            filename += f'_{self.year}'
        filename += '.xlsx'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_print_pdf(self):
        """Print report to PDF"""
        self.ensure_one()

        # Use the lines that are currently in the wizard
        allocations = self.allocation_line_ids
        expenses = self.expense_line_ids

        if not allocations and not expenses:
            raise UserError(_('No records to export. Please adjust your filters.'))

        data = {
            'wizard_id': self.id,
            'custodian_name': self.custodian_id.name if self.custodian_id else 'All Custodians',
            'year': self.year or 'All Years',
            'allocation_ids': allocations.ids,
            'expense_ids': expenses.ids,
            'amount_brought_forward': self.amount_brought_forward,
        }

        return self.env.ref('pct_petty_cash.action_report_cash_report').report_action(self, data=data)


class PctCashReportPdf(models.AbstractModel):
    _name = 'report.pct_petty_cash.report_cash_report_template'
    _description = 'Cash Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values for PDF"""
        if data is None:
            data = {}

        allocation_ids = data.get('allocation_ids', [])
        expense_ids = data.get('expense_ids', [])

        allocations = self.env['pct.petty.cash.allocation'].browse(allocation_ids)
        expenses = self.env['pct.petty.cash.expense'].browse(expense_ids)

        total_allocated = sum(allocations.mapped('amount'))
        total_expensed = sum(expenses.mapped('amount'))
        amount_brought_forward = data.get('amount_brought_forward', 0.0)

        return {
            'doc_ids': docids,
            'doc_model': 'pct.cash.report.wizard',
            'docs': self.env['pct.cash.report.wizard'].browse(docids),
            'data': data,
            'allocations': allocations,
            'expenses': expenses,
            'amount_brought_forward': amount_brought_forward,
            'total_allocated': total_allocated,
            'total_expensed': total_expensed,
            'balance': amount_brought_forward + total_allocated - total_expensed,
            'custodian_name': data.get('custodian_name', 'All Custodians'),
            'year': data.get('year', 'All Years'),
        }
