from odoo import fields, models
import base64
from io import BytesIO
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
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
            raise UserWarning('Python library openpyxl is not installed. Please install it to export Excel files.')

        # Get housing records
        housings = self.housing_ids if self.housing_ids else self.env['expatriate.housing'].browse(self._context.get('active_ids', []))

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Housing Report"

        # Define header style
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Write headers
        headers = ['Name', 'Date of Renewal', 'Num of days to Expire', 'Alert', 'Location / Type', 'Rent\nAmount', 'Maintenance Charge & Diesel', 'NEPA / Electricity']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Write data
        row_num = 2
        total_rent = 0
        total_maintenance = 0
        total_electricity = 0

        for housing in housings:
            # Get cost breakdown
            rent = 0
            maintenance = 0
            electricity = 0

            for cost_line in housing.cost_line_ids:
                line_name = (cost_line.name or '').lower()
                if 'rent' in line_name:
                    rent += cost_line.amount
                elif 'maintenance' in line_name or 'diesel' in line_name:
                    maintenance += cost_line.amount
                elif 'electric' in line_name or 'nepa' in line_name:
                    electricity += cost_line.amount

            total_rent += rent
            total_maintenance += maintenance
            total_electricity += electricity

            # Write row data
            ws.cell(row=row_num, column=1, value=housing.employee_id.name or '')
            ws.cell(row=row_num, column=2, value=housing.renewal_date.strftime('%d-%b-%Y') if housing.renewal_date else '')
            ws.cell(row=row_num, column=3, value=housing.days_to_expire)
            ws.cell(row=row_num, column=4, value=dict(housing._fields['alert_status'].selection).get(housing.alert_status, ''))
            ws.cell(row=row_num, column=5, value=f"{housing.location}\n{housing.housing_type or ''}")
            ws.cell(row=row_num, column=6, value=rent)
            ws.cell(row=row_num, column=7, value=maintenance)
            ws.cell(row=row_num, column=8, value=electricity)

            row_num += 1

        # Write totals
        row_num += 1
        ws.cell(row=row_num, column=6, value=total_rent).font = Font(bold=True)
        ws.cell(row=row_num, column=7, value=total_maintenance).font = Font(bold=True)
        ws.cell(row=row_num, column=8, value=total_electricity).font = Font(bold=True)

        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 18
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 25
        ws.column_dimensions['H'].width = 20

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Update wizard with file
        self.excel_file = base64.b64encode(output.read())
        self.filename = f'housing_report_{fields.Date.today()}.xlsx'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'housing.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
