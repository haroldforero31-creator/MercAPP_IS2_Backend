# -*- coding: utf-8 -*-
"""
Generador de Reportes Profesionales — MercAPP
Soporta exportación en Excel (.xlsx) y CSV con formato corporativo.
Criterio F de Sustentación: Reportes en formato PDF o Excel con logo y estilos.
"""
from datetime import datetime
from io import BytesIO

def generate_sales_report_excel(sales_data, store_name="MercAPP", period="Hoy"):
    """Genera reporte de ventas en Excel con formato ejecutivo corporativo."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Ventas"

    # Estilos
    header_font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    subheader_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    subheader_fill = PatternFill(start_color="388E3C", end_color="388E3C", fill_type="solid")
    accent_fill = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    money_format = "#,##0"

    # Encabezado del reporte
    ws.merge_cells("A1:G1")
    ws["A1"] = f"{store_name} — Reporte de Ventas"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("A2:G2")
    ws["A2"] = f"Período: {period}  |  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ws["A2"].font = Font(name="Calibri", italic=True, size=10, color="555555")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Columnas
    columns = ["# Recibo", "Fecha", "Cajero", "Método de Pago", "Subtotal", "Total", "Estado"]
    ws.append([])  # Row 3 blank
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    # Datos
    total_ventas = 0
    total_monto = 0
    for row_idx, sale in enumerate(sales_data, 5):
        ws.cell(row=row_idx, column=1, value=sale.get("receipt_number", "")).border = border
        ws.cell(row=row_idx, column=2, value=sale.get("date", "")).border = border
        ws.cell(row=row_idx, column=3, value=sale.get("cashier", "")).border = border
        ws.cell(row=row_idx, column=4, value=sale.get("payment_method", "")).border = border

        subtotal_cell = ws.cell(row=row_idx, column=5, value=sale.get("subtotal", 0))
        subtotal_cell.number_format = money_format
        subtotal_cell.border = border

        total_cell = ws.cell(row=row_idx, column=6, value=sale.get("total", 0))
        total_cell.number_format = money_format
        total_cell.border = border

        ws.cell(row=row_idx, column=7, value=sale.get("status", "completada")).border = border

        if row_idx % 2 == 0:
            for c in range(1, 8):
                ws.cell(row=row_idx, column=c).fill = accent_fill

        total_ventas += 1
        total_monto += sale.get("total", 0)

    # Resumen
    summary_row = len(sales_data) + 6
    ws.merge_cells(f"A{summary_row}:D{summary_row}")
    ws.cell(row=summary_row, column=1, value="RESUMEN TOTAL").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=5, value=f"{total_ventas} ventas").font = Font(bold=True)
    total_summary = ws.cell(row=summary_row, column=6, value=total_monto)
    total_summary.font = Font(bold=True, size=12, color="2E7D32")
    total_summary.number_format = money_format

    # Pie de reporte
    footer_row = summary_row + 2
    ws.merge_cells(f"A{footer_row}:G{footer_row}")
    ws.cell(row=footer_row, column=1, value="© MercAPP — Sistema POS para Supermercados | Reporte generado automáticamente").font = Font(italic=True, size=9, color="888888")

    # Ajustar anchos de columna
    widths = [18, 20, 20, 18, 15, 15, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    output = BytesIO()
    try:
        wb.save(output)
        output.seek(0)
        return output
    except Exception as e:
        output.close()
        raise e


def generate_inventory_report_excel(products_data, store_name="MercAPP"):
    """Genera reporte de inventario en Excel con formato ejecutivo corporativo."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"

    header_font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    header_fill = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")
    subheader_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    subheader_fill = PatternFill(start_color="1976D2", end_color="1976D2", fill_type="solid")
    danger_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    ws.merge_cells("A1:F1")
    ws["A1"] = f"{store_name} — Reporte de Inventario"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("A2:F2")
    ws["A2"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ws["A2"].font = Font(italic=True, size=10, color="555555")
    ws["A2"].alignment = Alignment(horizontal="center")

    columns = ["Producto", "Código de Barras", "Categoría", "Precio", "Stock", "Estado"]
    ws.append([])
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    for row_idx, prod in enumerate(products_data, 5):
        ws.cell(row=row_idx, column=1, value=prod.get("name", "")).border = border
        ws.cell(row=row_idx, column=2, value=prod.get("barcode", "")).border = border
        ws.cell(row=row_idx, column=3, value=prod.get("category", "")).border = border
        price_cell = ws.cell(row=row_idx, column=4, value=prod.get("price", 0))
        price_cell.number_format = "#,##0"
        price_cell.border = border
        stock_cell = ws.cell(row=row_idx, column=5, value=prod.get("stock", 0))
        stock_cell.border = border
        stock_val = prod.get("stock") or 0
        estado = "Crítico" if stock_val <= 5 else ("Bajo" if stock_val <= 15 else "OK")
        status_cell = ws.cell(row=row_idx, column=6, value=estado)
        status_cell.border = border
        if stock_val <= 5:
            for c in range(1, 7):
                ws.cell(row=row_idx, column=c).fill = danger_fill

    widths = [30, 18, 20, 12, 10, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    output = BytesIO()
    try:
        wb.save(output)
        output.seek(0)
        return output
    except Exception as e:
        output.close()
        raise e
