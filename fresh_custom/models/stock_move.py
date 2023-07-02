from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    qualifier_id = fields.Many2one("stock.lot.qualifier")
