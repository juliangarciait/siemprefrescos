from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credito_autorizado = fields.Float(string='Crédito Autorizado', groups="credit_limit.group_credit_limit", help='Crédito que se le ha autorizado al cliente.')
    credito_disponible = fields.Float(string='Crédito Disponible', compute='_compute_credito_disponible', store=True)

    @api.depends('credito_autorizado', 'invoice_ids.state')
    def _compute_credito_disponible(self):
        for partner in self:
            total_pendiente = sum(partner.invoice_ids.filtered(lambda inv: inv.state not in ['paid', 'cancel']).mapped('amount_total'))
            partner.credito_disponible = partner.credito_autorizado - total_pendiente

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            if order.partner_id.credito_disponible < order.amount_total:
                raise UserError("El cliente excedió el límite de crédito.")
        return super(SaleOrder, self).action_confirm()