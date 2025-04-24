from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def action_register_payment(self, ctx=None):
            ''' Open the account.payment.register wizard to pay the selected journal items.
            :return: An action opening the account.payment.register wizard.
            '''
            print("aqui")
            newlist = sorted(self.ids)
            context = {
                'active_model': 'account.move.line',
                'active_ids': newlist,
            }
            if ctx:
                context.update(ctx)
            return {
                'name': _('Pay'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'views': [[False, 'form']],
                'context': context,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }