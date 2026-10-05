# -*- coding: utf-8 -*-
{
    'name': "Reporte Detallado de Líneas de Venta, Facturas y Lotes",
    'summary': "Reporte y exportación a Excel de líneas de pedido vinculadas con facturas validadas, UUID fiscal, lotes y albaranes de salida.",
    'description': """
Reporte Detallado de Ventas y Facturación
=========================================
Este módulo genera un reporte detallado con las siguientes características:
- Vincula cada línea de pedido (sale.order.line) con su línea de factura (account.move.line).
- Filtra automáticamente facturas validadas (excluye borrador y canceladas).
- Extrae el RFC / ID Fiscal directamente del cliente en la factura (partner_id.vat).
- Muestra el Folio Fiscal (l10n_mx_edi_cfdi_uuid).
- Muestra el Lote de la línea de venta (lot_id).
- Muestra la Referencia del albarán de inventario (stock.picking) en estado Realizado ('done').
- Permite visualización en Lista (Tree), Pivot y exportación nativa o descarga directa en Excel (.xlsx).
    """,
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'account',
        'stock',
        'sale_stock',
        'sales_with_lots',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_invoice_report_views.xml',
        'wizard/sale_invoice_report_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
