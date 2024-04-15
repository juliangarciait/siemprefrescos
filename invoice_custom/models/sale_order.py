from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(SaleOrder, self)._create_invoices( grouped=False, final=False, date=None)
        for invoice in res:
            if invoice.partner_id.l10n_mx_edi_usage:
                invoice.l10n_mx_edi_usage = invoice.partner_id.l10n_mx_edi_usage
