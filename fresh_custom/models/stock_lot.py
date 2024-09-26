from odoo import models, api, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    qualifier_id = fields.Many2one("stock.lot.qualifier")
