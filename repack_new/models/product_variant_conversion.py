from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductVariantConversion(models.Model):
    _name = 'product.variant.conversion'
    _description = 'Product Variant Conversion'

    name = fields.Char(string='Reference', required=True, copy=False, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Source Product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Source Lot', required=True)
    conversion_lines = fields.One2many('product.variant.conversion.line', 'conversion_id', string='Conversion Lines')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('product.variant.conversion') or _('New')
        return super(ProductVariantConversion, self).create(vals)

    def action_confirm(self):
        self.ensure_one()
        if not self.conversion_lines:
            raise UserError(_("Please add conversion lines."))

        # 1. Crear/Obtener lotes para las variantes de destino
        source_lot_name = self.lot_id.name
        if not source_lot_name:
            raise UserError(_("The source lot must have a name."))

        # Assuming the source lot name follows the pattern:  04ABC25-0001XL
        # Extract the base part (04ABC25-0001)
        base_lot_name = '-'.join(source_lot_name.split('-')[:-1])

        for line in self.conversion_lines:
            # Construct the expected lot name for the destination variant
            variant_code = line.product_id.default_code or line.product_id.name  # Use default code or name as variant identifier
            if not variant_code or variant_code == "":
                raise UserError(_(f"Variant {line.product_id.name} must have an internal reference or name."))

            expected_lot_name = f"{base_lot_name}{variant_code[-2:] if len(variant_code) > 2 else variant_code}"  # Assuming last 2 chars of default code or name as variant identifier

            # Search for an existing lot with the expected name
            existing_lot = self.env['stock.production.lot'].search([
                ('name', '=', expected_lot_name),
                ('product_id', '=', line.product_id.id)
            ], limit=1)

            if existing_lot:
                line.lot_id = existing_lot
            else:
                line.lot_id = self.env['stock.lot'].create({
                    'product_id': line.product_id.id,
                    'name': expected_lot_name,
                    'company_id': self.company_id.id,  # Assuming you have a company_id field
                    'analytic_tag_ids': self.lot_id.analytic_tag_ids.ids,  # Copy analytic tags
                })

        # 2. Ajustes de inventario
        location_id = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)  # Ubicación interna por defecto
        if not location_id:
            raise UserError(_("No internal location found. Please create one."))

        inventory = self.env['stock.inventory'].create({
            'name': f'Conversion from {self.product_id.name} - Lot {self.lot_id.name}',
            'location_ids': [(6, 0, [location_id.id])],
            'state': 'confirm',
        })

        inventory.line_ids = [(0, 0, {
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'product_qty': -1 * self.lot_id.quantity,  # Descontar del lote original
            'location_id': location_id.id,
            'prod_lot_id': self.lot_id.id,
        })]

        for line in self.conversion_lines:
            inventory.line_ids += [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_id.uom_id.id,
                'product_qty': line.quantity,
                'location_id': location_id.id,
                'prod_lot_id': line.lot_id.id,
            })]

        inventory.action_validate()

        # 3. Pasar cantidades a la orden de venta (si existe)
        if self.sale_order_id:
            for line in self.conversion_lines:
                self.sale_order_id.order_line.filtered(lambda l: l.product_id == line.product_id).write({'product_uom_qty': line.quantity})

        self.state = 'done'


class ProductVariantConversionLine(models.Model):
    _name = 'product.variant.conversion.line'
    _description = 'Product Variant Conversion Line'

    conversion_id = fields.Many2one('product.variant.conversion', string='Conversion', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Variant', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot')
