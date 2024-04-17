from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'   
    
    
    @api.model_create_multi
    def create(self, vals_list):
        new_recs = super(AccountAnalyticAccount, self).create(vals_list)
        return new_recs