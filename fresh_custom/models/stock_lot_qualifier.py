from odoo import models, api, fields


class StockLotQualifier(models.Model):
    _name = 'stock.lot.qualifier'

    name = fields.Char()
