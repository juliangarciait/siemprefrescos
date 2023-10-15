from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    user_id = fields.Many2one(
        'res.users', 'Responsible', tracking=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('stock.group_stock_user').id)],
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        default=lambda self: self.env.user.has_group(
            'fresh_custom.fresh_stock_operation_without_permision_group') and self.picking_type_code == "incoming" and self.env.user)

    @api.depends('state')
    def _compute_show_validate(self):
        for picking in self:
            if not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned'):
                picking.show_validate = False
            else:
                picking.show_validate = True
            if picking.picking_type_code == "incoming" and self.env.user.has_group('fresh_custom.fresh_stock_operation_without_permision_group'):
                picking.show_validate = False
    
