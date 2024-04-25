from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_print_copy(self):
        return self.env.ref('account.account_invoices').report_action(self)