from odoo import api, fields, models
import re

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    lot = fields.Text(compute="_get_lot")

    @api.depends('order_line')
    def _get_lot(self):
        for order in self:
            order.lot = ''
            try:
                #purchase = self.env['purchase.order'].search([('invoice_ids', 'in', [order.id])])  
                picking = self.env['stock.picking'].search([('purchase_id', '=', order.id), ('state', '=', 'done')], order='create_date desc', limit=1)
                move = self.env['stock.move.line'].search([('picking_id', '=', picking.id)], limit=1)
                reference = move.lot_id.name
                if reference and picking.date_done:
                    patron = re.search(r'[a-zA-Z].*\d', reference)
                    if patron:
                        order.lot = patron.group()
                    else:
                        order.lot =""
            except:
                order.lot = ''



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    total_invoiced = fields.Float(compute='_compute_total_invoiced', string="Billed Total", store=True)
    purchase_lot = fields.Many2one('stock.lot', 'Lote')

    @api.depends('invoice_lines.price_unit', 'invoice_lines.quantity')
    def _compute_total_invoiced(self):
        for line in self:
            total = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        total += inv_line.price_total
                    elif inv_line.move_id._move_type == 'in_refund':
                        total -= inv_line.price_total
            line.total_invoiced = total