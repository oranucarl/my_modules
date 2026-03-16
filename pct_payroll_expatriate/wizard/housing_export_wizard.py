from odoo import fields, models
from odoo.exceptions import UserError
import base64
from io import BytesIO
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    Workbook = None


class HousingExportWizard(models.TransientModel):
    _name = 'housing.export.wizard'
    _description = 'Housing Export Wizard'

    housing_ids = fields.Many2many(
        'expatriate.housing',
        string='Housing Records'
    )
    excel_file = fields.Binary(
        string='Excel File',
        readonly=True
    )
    filename = fields.Char(
        string='Filename',
        default='housing_report.xlsx'
    )

    def action_export(self):
        """Generate Excel report"""
        if not Workbook:
            raise UserError('Python library openpyxl is not installed. Please install it to export Excel files.')

        # Get housing records
        housings = self.housing_ids
        if not housings:
            raise UserError('No housing records to export.')

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Housing Report"

        # Define styles
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell_alignment = Alignment(vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Write headers
        headers = ['Employee Name', 'Date of Renewal', 'Days to Expire', 'Alert Status', 'Location / Type', 'Rent', 'Maintenance Charge & Diesel', 'NEPA / Electricity', 'Total Cost']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border

        # Get product references for cost categorization
        rent_product = self.env.ref('pct_payroll_expatriate.product_housing_rent', raise_if_not_found=False)
        maintenance_product = self.env.ref('pct_payroll_expatriate.product_housing_maintenance', raise_if_not_found=False)
        electricity_product = self.env.ref('pct_payroll_expatriate.product_housing_electricity', raise_if_not_found=False)

        # Write data
        row_num = 2
        total_rent = 0
        total_maintenance = 0
        total_electricity = 0
        grand_total = 0

        for housing in housings:
            # Get cost breakdown by product
            rent = 0
            maintenance = 0
            electricity = 0

            for cost_line in housing.cost_line_ids:
                if cost_line.product_id:
                    if rent_product and cost_line.product_id.id == rent_product.id:
                        rent += cost_line.amount
                    elif maintenance_product and cost_line.product_id.id == maintenance_product.id:
                        maintenance += cost_line.amount
                    elif electricity_product and cost_line.product_id.id == electricity_product.id:
                        electricity += cost_line.amount
                    else:
                        # Fallback: categorize by product name
                        product_name = (cost_line.product_id.name or '').lower()
                        if 'rent' in product_name:
                            rent += cost_line.amount
                        elif 'maintenance' in product_name or 'diesel' in product_name:
                            maintenance += cost_line.amount
                        elif 'electric' in product_name or 'nepa' in product_name:
                            electricity += cost_line.amount

            row_total = rent + maintenance + electricity
            total_rent += rent
            total_maintenance += maintenance
            total_electricity += electricity
            grand_total += row_total

            # Get alert status display value
            alert_status_display = ''
            if housing.alert_status:
                alert_status_display = dict(housing._fields['alert_status'].selection).get(housing.alert_status, '')

            # Write row data
            location_type = housing.location or ''
            if housing.housing_type:
                location_type += f"\n{housing.housing_type}"

            row_data = [
                housing.employee_id.name or '',
                housing.renewal_date.strftime('%d-%b-%Y') if housing.renewal_date else '',
                housing.days_to_expire,
                alert_status_display,
                location_type,
                rent,
                maintenance,
                electricity,
                row_total
            ]

            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.alignment = cell_alignment
                cell.border = thin_border

            row_num += 1

        # Write totals row
        total_row = row_num
        ws.cell(row=total_row, column=1, value='TOTALS').font = Font(bold=True)
        ws.cell(row=total_row, column=1).border = thin_border

        for col in range(2, 6):
            ws.cell(row=total_row, column=col, value='').border = thin_border

        totals = [total_rent, total_maintenance, total_electricity, grand_total]
        for col_num, total_value in enumerate(totals, 6):
            cell = ws.cell(row=total_row, column=col_num, value=total_value)
            cell.font = Font(bold=True)
            cell.border = thin_border

        # Adjust column widths
        column_widths = [25, 15, 15, 12, 30, 15, 25, 20, 15]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        wb.close()  # Properly close the workbook
        output.seek(0)

        # Update wizard with file
        self.excel_file = base64.b64encode(output.read())
        self.filename = f'housing_report_{fields.Date.today()}.xlsx'
        output.close()  # Close the BytesIO

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'housing.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
