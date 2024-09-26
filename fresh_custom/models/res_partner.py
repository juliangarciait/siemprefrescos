from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    owner_id = fields.Many2one("res.users", default=lambda self: self.env.user)