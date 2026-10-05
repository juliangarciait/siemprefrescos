# -*- coding: utf-8 -*-
import io
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xlsxwriter

class SaleInvoiceReportWizard(models.TransientModel):
    _name = 'sale.invoice.report.wizard'
    _description = 'Asistente de Exportación a Excel de Ventas y Facturas'

    date_from = fields.Datetime(string="Fecha Desde")
    date_to = fields.Datetime(string="Fecha Hasta")
    partner_ids = fields.Many2many('res.partner', string="Clientes")
    order_ids = fields.Many2many('sale.order', string="Órdenes de Venta")

    excel_file = fields.Binary(string="Archivo Excel", readonly=True)
    file_name = fields.Char(string="Nombre de Archivo", readonly=True)

    def _get_domain(self):
        domain = []
        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.order_ids:
            domain.append(('order_id', 'in', self.order_ids.ids))
        return domain

    def action_view_records(self):
        domain = self._get_domain()
        action = self.env.ref('sale_order_invoice_report.action_sale_invoice_report').read()[0]
        action['domain'] = domain
        return action

    def action_export_excel(self):
        domain = self._get_domain()
        records = self.env['sale.invoice.report'].search(domain)
        if not records:
            raise UserError(_("No se encontraron registros para los filtros seleccionados."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Ventas y Facturas')

        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#EFEFEF',
            'bottom': 1
        })
        text_format = workbook.add_format({'valign': 'vcenter'})
        num_format = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        percent_format = workbook.add_format({'valign': 'vcenter', 'align': 'right'})

        headers = [
            'Orden', 'Fecha de creación', 'Referencia', 'Cliente', 
            'RFC/ID FISCAL', 'Moneda', 'Folio Fiscal', 'Producto', 
            'Lote', 'Cantidad', 'Medida', 'Precio Unit.', 
            'Subtotal', 'IVA', 'Total'
        ]

        for col_idx, header in enumerate(headers):
            worksheet.write(0, col_idx, header, header_format)

        for row_idx, rec in enumerate(records, start=1):
            worksheet.write(row_idx, 0, rec.order_name or '', text_format)
            if rec.date_order:
                worksheet.write(row_idx, 1, rec.date_order.strftime('%Y-%m-%d %H:%M:%S'), text_format)
            else:
                worksheet.write(row_idx, 1, '', text_format)
            worksheet.write(row_idx, 2, rec.picking_ref or '', text_format)
            worksheet.write(row_idx, 3, rec.partner_id.name or '', text_format)
            worksheet.write(row_idx, 4, rec.partner_vat or '', text_format)
            worksheet.write(row_idx, 5, rec.currency_id.name or '', text_format)
            worksheet.write(row_idx, 6, rec.folio_fiscal or '', text_format)
            worksheet.write(row_idx, 7, rec.product_id.display_name or '', text_format)
            worksheet.write(row_idx, 8, rec.lot_id.name or '', text_format)
            worksheet.write(row_idx, 9, rec.quantity or 0.0, num_format)
            worksheet.write(row_idx, 10, rec.uom_id.name or '', text_format)
            worksheet.write(row_idx, 11, rec.price_unit or 0.0, num_format)
            worksheet.write(row_idx, 12, rec.price_subtotal or 0.0, num_format)
            worksheet.write(row_idx, 13, rec.tax_rate or '0%', percent_format)
            worksheet.write(row_idx, 14, rec.price_total or 0.0, num_format)

        worksheet.autofit()
        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        self.write({
            'excel_file': file_data,
            'file_name': 'Reporte_Ventas_Facturas.xlsx'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=excel_file&download=true&filename={self.file_name}',
            'target': 'self',
        }
