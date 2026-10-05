# -*- coding: utf-8 -*-
from odoo import models, fields, tools

class SaleInvoiceReport(models.Model):
    _name = "sale.invoice.report"
    _description = "Reporte Detallado de Líneas de Venta, Facturas y Lotes"
    _auto = False
    _order = "date_order desc, order_name desc, id desc"

    # Datos de la Orden de Venta
    order_id = fields.Many2one('sale.order', string="Orden de Venta", readonly=True)
    order_name = fields.Char(string="Orden", readonly=True)
    date_order = fields.Datetime(string="Fecha de creación", readonly=True)
    picking_ref = fields.Char(string="Referencia", readonly=True)

    # Datos de la Factura y Cliente
    move_id = fields.Many2one('account.move', string="Factura", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Cliente", readonly=True)
    partner_vat = fields.Char(string="RFC/ID FISCAL", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", readonly=True)
    folio_fiscal = fields.Char(string="Folio Fiscal", readonly=True)

    # Producto y Lote
    product_id = fields.Many2one('product.product', string="Producto", readonly=True)
    lot_id = fields.Many2one('stock.lot', string="Lote", readonly=True)

    # Importes y Cantidades
    quantity = fields.Float(string="Cantidad", readonly=True)
    uom_id = fields.Many2one('uom.uom', string="Medida", readonly=True)
    price_unit = fields.Float(string="Precio Unit.", readonly=True)
    price_subtotal = fields.Monetary(string="Subtotal", currency_field="currency_id", readonly=True)
    tax_rate = fields.Char(string="IVA", readonly=True)
    tax_amount = fields.Monetary(string="Monto IVA", currency_field="currency_id", readonly=True)
    price_total = fields.Monetary(string="Total", currency_field="currency_id", readonly=True)

    # Trazabilidad técnica
    sale_line_id = fields.Many2one('sale.order.line', string="Línea de Venta", readonly=True)
    invoice_line_id = fields.Many2one('account.move.line', string="Línea de Factura", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        # Validación dinámica para Folio Fiscal SAT (l10n_mx_edi_cfdi_uuid)
        self.env.cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'account_move' AND column_name = 'l10n_mx_edi_cfdi_uuid'
        """)
        has_uuid = bool(self.env.cr.fetchone())
        uuid_expr = "am.l10n_mx_edi_cfdi_uuid" if has_uuid else "NULL::varchar"

        # Validación dinámica para campo de lote en sale.order.line
        self.env.cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'sale_order_line' AND column_name = 'lot_id'
        """)
        has_lot = bool(self.env.cr.fetchone())
        lot_expr = "sol.lot_id" if has_lot else "NULL::integer"

        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY so.date_order DESC NULLS LAST, so.name DESC, sol.id, aml.id) AS id,
                    so.id AS order_id,
                    so.name AS order_name,
                    so.date_order AS date_order,
                    COALESCE(
                        (
                            SELECT STRING_AGG(DISTINCT sp.name, ', ' ORDER BY sp.name)
                            FROM stock_move sm
                            JOIN stock_picking sp ON sp.id = sm.picking_id
                            WHERE sm.sale_line_id = sol.id
                              AND sp.state = 'done'
                        ),
                        (
                            SELECT STRING_AGG(DISTINCT sp.name, ', ' ORDER BY sp.name)
                            FROM stock_picking sp
                            WHERE sp.sale_id = so.id
                              AND sp.state = 'done'
                        )
                    ) AS picking_ref,
                    am.id AS move_id,
                    am.partner_id AS partner_id,
                    p.vat AS partner_vat,
                    am.currency_id AS currency_id,
                    {uuid_expr} AS folio_fiscal,
                    sol.product_id AS product_id,
                    {lot_expr} AS lot_id,
                    aml.quantity AS quantity,
                    aml.product_uom_id AS uom_id,
                    aml.price_unit AS price_unit,
                    aml.price_subtotal AS price_subtotal,
                    CASE 
                        WHEN aml.price_subtotal IS NOT NULL AND aml.price_subtotal != 0 THEN 
                            ROUND(ABS((aml.price_total - aml.price_subtotal) / aml.price_subtotal * 100)::numeric, 0)::text || '%'
                        ELSE '0%'
                    END AS tax_rate,
                    (aml.price_total - aml.price_subtotal) AS tax_amount,
                    aml.price_total AS price_total,
                    sol.id AS sale_line_id,
                    aml.id AS invoice_line_id
                FROM sale_order_line sol
                JOIN sale_order so ON so.id = sol.order_id
                JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
                JOIN account_move_line aml ON aml.id = rel.invoice_line_id
                JOIN account_move am ON am.id = aml.move_id
                JOIN res_partner p ON p.id = am.partner_id
                WHERE am.state = 'posted'
                  AND am.move_type IN ('out_invoice', 'out_refund')
                  AND (aml.display_type IS NULL OR aml.display_type NOT IN ('line_section', 'line_note'))
            )
        """)
