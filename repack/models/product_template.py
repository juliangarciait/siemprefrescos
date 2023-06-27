from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_fabricacion = fields.Many2one('product.template', string='Producto Limpio')