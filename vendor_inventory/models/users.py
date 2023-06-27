from odoo import api, fields, models

class Users(models.Model):
    _inherit = 'res.users'
    
    default_warehouse_id = fields.Many2one('stock.location', string='Default Warehouse')