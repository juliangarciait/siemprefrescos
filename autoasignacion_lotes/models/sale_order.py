from odoo import api, fields, models, SUPERUSER_ID, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_tag_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Tags',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        dict_analytic = {'analytic_distribution':{}}
        dict_analytic['analytic_distribution'].update({str(tag.id): 100 for tag in self.lot_id.analytic_tag_ids})
        res.update(dict_analytic)
        return res
    
    # @api.onchange('lot_id', 'product_id')
    # def _onchange_lot_sel_account(self):
    #     if self.lot_id and self.lot_id.analytic_tag_ids:
    #         self.analytic_tag_ids = False
    #         self.analytic_tag_ids = [(4, tag.id) for tag in self.lot_id.analytic_tag_ids]
    #         no esta guardando revisar despues

