from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def action_post(self):
        # Call the super method to ensure the original functionality is preserved
        super(AccountMove, self).action_post()
        
        if self.journal_id.timbrar_mx:
            self.ensure_one()
            self.env['account.move.send']._generate_and_send_invoices(self, sending_methods=['manual'], extra_edis={'mx_cfdi'})
