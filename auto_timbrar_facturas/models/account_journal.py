from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    timbrar_mx = fields.Boolean(string="Timbrar MX")