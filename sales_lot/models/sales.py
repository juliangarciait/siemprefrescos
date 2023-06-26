# -*- coding: utf-8 -*-
from xml.dom import ValidationErr
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

import logging


_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    tracking = fields.Selection(related='product_id.tracking', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lot', copy=False)
    #lot_available_sell = fields.Float('Stock', readonly=1)
    #custom_state_delivery = fields.Char(related='order_id.custom_state_delivery')