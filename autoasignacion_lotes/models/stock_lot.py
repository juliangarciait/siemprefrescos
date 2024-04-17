from odoo import api, fields, models


class LotData(models.Model):
    _inherit = 'stock.lot'

    analytic_tag_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Tags',
        help="This field contains the information related to the account tags for this lot",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")