from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, Reference, BarChart
from io import BytesIO
import pandas as pd
from datetime import datetime

class RetirementExcelExporter:
    """Export retirement projections to Excel format"""
    
    def __init__(self):
        self.workbook = Workbook()
        self.setup_styles()
    
    def setup_styles(self):
        """Setup common styles for the Excel file"""
        self.title_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        self.header_font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        self.data_font = Font(name='Arial', size=10)
        self.currency_font = Font(name='Arial', size=10)
        
        self.title_fill = PatternFill(start_color='2E75B6', end_color='2E75B6', fill_type='solid')
        self.header_fill = PatternFill(start_color='5B9BD5', end_color='5B9BD5', fill_type='solid')
        self.positive_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
        self.negative_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        
        self.center_alignment = Alignment(horizontal='center', vertical='center')
        self.currency_alignment = Alignment(horizontal='right', vertical='center')
        
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    def export_projection(self, projection_data, summary_stats, scenario_name=None):
        """Export complete retirement projection to Excel"""
        # Remove default worksheet
        self.workbook.remove(self.workbook.active)
        
        # Create worksheets
        self.create_summary_sheet(summary_stats, scenario_name)
        self.create_yearly_data_sheet(projection_data)
        self.create_account_breakdown_sheet(projection_data)
        self.create_cash_flow_sheet(projection_data)
        self.create_charts_sheet(projection_data)
        
        # Save to BytesIO
        output = BytesIO()
        self.workbook.save(output)
        output.seek(0)
        
        return output
    
    def create_summary_sheet(self, summary_stats, scenario_name):
        """Create summary statistics sheet"""
        ws = self.workbook.create_sheet('Summary', 0)
        
        # Title
        ws['A1'] = scenario_name or 'Retirement Projection Summary'
        ws['A1'].font = self.title_font
        ws['A1'].fill = self.title_fill
        ws['A1'].alignment = self.center_alignment
        ws.merge_cells('A1:D1')
        
        # Generation info
        ws['A2'] = f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        ws['A2'].font = Font(name='Arial', size=9, italic=True)
        
        # Summary statistics
        row = 4
        ws[f'A{row}'] = 'Key Metrics'
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].fill = self.header_fill
        ws.merge_cells(f'A{row}:D{row}')
        
        metrics = [
            ('Final Balance', summary_stats.get('final_balance', 0)),
            ('Total Contributions', summary_stats.get('total_contributions', 0)),
            ('Total Withdrawals', summary_stats.get('total_withdrawals', 0)),
            ('Total Taxes Paid', summary_stats.get('total_taxes_paid', 0)),
            ('Years Simulated', summary_stats.get('years_simulated', 0)),
        ]
        
        for i, (metric, value) in enumerate(metrics, start=row+1):
            ws[f'A{i}'] = metric
            ws[f'A{i}'].font = self.data_font
            ws[f'A{i}'].border = self.thin_border
            
            if metric == 'Years Simulated':
                ws[f'B{i}'] = value
                ws[f'B{i}'].number_format = '0'
            else:
                ws[f'B{i}'] = value
                ws[f'B{i}'].number_format = '"$"#,##0'
            
            ws[f'B{i}'].font = self.currency_font
            ws[f'B{i}'].alignment = self.currency_alignment
            ws[f'B{i}'].border = self.thin_border
            
            # Color coding for positive/negative values
            if isinstance(value, (int, float)) and value < 0:
                ws[f'B{i}'].fill = self.negative_fill
            elif isinstance(value, (int, float)) and value > 0:
                ws[f'B{i}'].fill = self.positive_fill
        
        # Auto-fit columns
        for col in ['A', 'B', 'C', 'D']:
            ws.column_dimensions[col].width = 20
    
    def create_yearly_data_sheet(self, projection_data):
        """Create detailed yearly data sheet"""
        ws = self.workbook.create_sheet('Yearly Data')
        
        # Title
        ws['A1'] = 'Year-by-Year Projection'
        ws['A1'].font = self.title_font
        ws['A1'].fill = self.title_fill
        ws['A1'].alignment = self.center_alignment
        ws.merge_cells('A1:J1')
        
        # Headers
        headers = [
            'Age', 'Calendar Year', 'Income', 'Expenses', 'Total Balance',
            'Contributions', 'Withdrawals', 'Taxes Paid', 'Shortfall', 'Net Cash Flow'
        ]
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        # Data rows
        for row_idx, year_data in enumerate(projection_data, start=4):
            data = [
                year_data.get('age', 0),
                year_data.get('calendar_year', year_data.get('age', 0) + 1990),  # Fallback calculation
                year_data.get('income', 0),
                year_data.get('expenses', 0),
                year_data.get('total_account_balance', 0),
                year_data.get('total_contributions', 0),
                year_data.get('total_withdrawals', 0),
                year_data.get('taxes_paid', 0),
                year_data.get('shortfall', 0),
                year_data.get('net_cash_flow', 0)
            ]
            
            for col_idx, value in enumerate(data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.font = self.data_font
                cell.border = self.thin_border
                
                # Format numbers
                if col_idx == 1:  # Age
                    cell.number_format = '0'
                elif col_idx == 2:  # Calendar Year
                    cell.number_format = '0'
                else:  # Currency values
                    cell.number_format = '"$"#,##0'
                    cell.alignment = self.currency_alignment
                
                # Color coding
                if isinstance(value, (int, float)):
                    if col_idx == 9 and value > 0:  # Shortfall
                        cell.fill = self.negative_fill
                    elif col_idx == 10 and value < 0:  # Negative cash flow
                        cell.fill = self.negative_fill
                    elif col_idx in [6, 7] and value > 0:  # Contributions, withdrawals
                        cell.fill = self.positive_fill
        
        # Auto-fit columns
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def create_account_breakdown_sheet(self, projection_data):
        """Create account-by-account breakdown sheet"""
        ws = self.workbook.create_sheet('Account Breakdown')
        
        # Title
        ws['A1'] = 'Account Balance Breakdown'
        ws['A1'].font = self.title_font
        ws['A1'].fill = self.title_fill
        ws['A1'].alignment = self.center_alignment
        
        # Find all account types
        account_types = set()
        for year_data in projection_data:
            for key in year_data.keys():
                if key.endswith('_balance') and key != 'total_account_balance':
                    account_type = key.replace('_balance', '')
                    account_types.add(account_type)
        
        account_types = sorted(list(account_types))
        
        # Headers
        headers = ['Age', 'Calendar Year'] + [f'{acc.replace("_", " ").title()}' for acc in account_types] + ['Total']
        
        # Merge title across all columns
        ws.merge_cells(f'A1:{get_column_letter(len(headers))}1')
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        # Data rows
        for row_idx, year_data in enumerate(projection_data, start=4):
            # Basic info
            ws.cell(row=row_idx, column=1).value = year_data.get('age', 0)
            ws.cell(row=row_idx, column=2).value = year_data.get('calendar_year', year_data.get('age', 0) + 1990)
            
            # Account balances
            for col_idx, account_type in enumerate(account_types, start=3):
                balance = year_data.get(f'{account_type}_balance', 0)
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = balance
                cell.number_format = '"$"#,##0'
                cell.alignment = self.currency_alignment
                cell.font = self.data_font
                cell.border = self.thin_border
                
                if balance > 0:
                    cell.fill = self.positive_fill
            
            # Total
            total_col = len(account_types) + 3
            total_cell = ws.cell(row=row_idx, column=total_col)
            total_cell.value = year_data.get('total_account_balance', 0)
            total_cell.number_format = '"$"#,##0'
            total_cell.alignment = self.currency_alignment
            total_cell.font = Font(name='Arial', size=10, bold=True)
            total_cell.border = self.thin_border
            
            # Format age and year columns
            ws.cell(row=row_idx, column=1).number_format = '0'
            ws.cell(row=row_idx, column=2).number_format = '0'
            ws.cell(row=row_idx, column=1).font = self.data_font
            ws.cell(row=row_idx, column=2).font = self.data_font
            ws.cell(row=row_idx, column=1).border = self.thin_border
            ws.cell(row=row_idx, column=2).border = self.thin_border
        
        # Auto-fit columns
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def create_cash_flow_sheet(self, projection_data):
        """Create cash flow analysis sheet"""
        ws = self.workbook.create_sheet('Cash Flow Analysis')
        
        # Title
        ws['A1'] = 'Cash Flow Analysis'
        ws['A1'].font = self.title_font
        ws['A1'].fill = self.title_fill
        ws['A1'].alignment = self.center_alignment
        ws.merge_cells('A1:H1')
        
        # Headers
        headers = [
            'Age', 'Income', 'Expenses', 'Available Savings', 'Total Contributions',
            'Total Withdrawals', 'Taxes Paid', 'Net Cash Flow'
        ]
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        # Data rows
        for row_idx, year_data in enumerate(projection_data, start=4):
            data = [
                year_data.get('age', 0),
                year_data.get('income', 0),
                year_data.get('expenses', 0),
                year_data.get('available_savings', 0),
                year_data.get('total_contributions', 0),
                year_data.get('total_withdrawals', 0),
                year_data.get('taxes_paid', 0),
                year_data.get('net_cash_flow', 0)
            ]
            
            for col_idx, value in enumerate(data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.font = self.data_font
                cell.border = self.thin_border
                
                if col_idx == 1:  # Age
                    cell.number_format = '0'
                else:  # Currency values
                    cell.number_format = '"$"#,##0'
                    cell.alignment = self.currency_alignment
                
                # Color coding
                if isinstance(value, (int, float)):
                    if col_idx == 8 and value < 0:  # Negative cash flow
                        cell.fill = self.negative_fill
                    elif col_idx in [4, 5] and value > 0:  # Positive savings/contributions
                        cell.fill = self.positive_fill
        
        # Auto-fit columns
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def create_charts_sheet(self, projection_data):
        """Create charts visualization sheet"""
        ws = self.workbook.create_sheet('Charts')
        
        # Title
        ws['A1'] = 'Projection Charts'
        ws['A1'].font = self.title_font
        ws['A1'].fill = self.title_fill
        ws['A1'].alignment = self.center_alignment
        ws.merge_cells('A1:J1')
        
        # Prepare data for charts
        ages = [year_data.get('age', 0) for year_data in projection_data]
        balances = [year_data.get('total_account_balance', 0) for year_data in projection_data]
        
        # Create data table for chart
        ws['A3'] = 'Age'
        ws['B3'] = 'Total Balance'
        ws['C3'] = 'Income'
        ws['D3'] = 'Expenses'
        
        for i, year_data in enumerate(projection_data, start=4):
            ws[f'A{i}'] = year_data.get('age', 0)
            ws[f'B{i}'] = year_data.get('total_account_balance', 0)
            ws[f'C{i}'] = year_data.get('income', 0)
            ws[f'D{i}'] = year_data.get('expenses', 0)
        
        # Create line chart for account balance
        chart1 = LineChart()
        chart1.title = "Account Balance Over Time"
        chart1.y_axis.title = "Balance ($)"
        chart1.x_axis.title = "Age"
        
        # Add data to chart
        data_range = len(projection_data) + 3
        data = Reference(ws, min_col=2, min_row=3, max_row=data_range)
        categories = Reference(ws, min_col=1, min_row=4, max_row=data_range)
        
        chart1.add_data(data, titles_from_data=True)
        chart1.set_categories(categories)
        
        # Style the chart
        chart1.width = 15
        chart1.height = 10
        
        # Add chart to worksheet
        ws.add_chart(chart1, "F3")
        
        # Create income/expense chart
        chart2 = LineChart()
        chart2.title = "Income vs Expenses"
        chart2.y_axis.title = "Amount ($)"
        chart2.x_axis.title = "Age"
        
        # Add income and expense data
        income_data = Reference(ws, min_col=3, min_row=3, max_row=data_range)
        expense_data = Reference(ws, min_col=4, min_row=3, max_row=data_range)
        
        chart2.add_data(income_data, titles_from_data=True)
        chart2.add_data(expense_data, titles_from_data=True)
        chart2.set_categories(categories)
        
        # Style the chart
        chart2.width = 15
        chart2.height = 10
        
        # Add chart to worksheet
        ws.add_chart(chart2, "F20")

def create_excel_export(projection_data, summary_stats, scenario_name=None):
    """Create Excel export for retirement projection"""
    exporter = RetirementExcelExporter()
    return exporter.export_projection(projection_data, summary_stats, scenario_name)