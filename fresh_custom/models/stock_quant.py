from odoo import models, fields


class StockQuant(models.Model):
    _inherit = "stock.quant"

    qualifier_id = fields.Many2one("stock.lot.qualifier", related="lot_id.qualifier_id")
