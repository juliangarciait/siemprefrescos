from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductVariantConversionWizard(models.TransientModel):
    _name = 'product.variant.conversion.wizard'
    _description = 'Product Variant Conversion Wizard'

    product_id = fields.Many2one('product.product', string='Source Product', required=True, domain="[('type', '=', 'product')]")
    lot_id = fields.Many2one('stock.production.lot', string='Source Lot', required=True)
    conversion_lines = fields.One2many('product.variant.conversion.wizard.line', 'wizard_id', string='Conversion Lines')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    quantity = fields.Float(string='Quantity', default=0.0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            variants = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id), ('id', '!=', self.product_id.id)])
            lines = [(0, 0, {'product_id': variant.id}) for variant in variants]
            self.conversion_lines = lines
        else:
            self.conversion_lines = False

    def action_convert(self):
        self.ensure_one()
        if not self.conversion_lines.filtered(lambda l: l.quantity > 0):
            raise UserError(_("Please specify quantities for at least one variant."))

        conversion = self.env['product.variant.conversion'].create({
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'sale_order_id': self.sale_order_id.id,
            'conversion_lines': [(0, 0, {'product_id': line.product_id.id, 'quantity': line.quantity}) for line in self.conversion_lines if line.quantity > 0],
        })
        conversion.action_confirm()
        return {'type': 'ir.actions.act_window_close'}


class ProductVariantConversionWizardLine(models.TransientModel):
    _name = 'product.variant.conversion.wizard.line'
    _description = 'Product Variant Conversion Wizard Line'

    wizard_id = fields.Many2one('product.variant.conversion.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Variant', required=True, readonly=True)
    quantity = fields.Float(string='Quantity', default=0.0)
