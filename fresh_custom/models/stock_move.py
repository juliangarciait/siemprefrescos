import logging

from odoo import models, fields
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    qualifier_id = fields.Many2one("stock.lot.qualifier")
    product_avalaible_stock = fields.Float(related="product_id.immediately_usable_qty")
