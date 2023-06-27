from odoo import api, fields, models

class StockPicking1(models.Model):
    _inherit = 'stock.picking'
    
    is_vendor = fields.Boolean(string='Es Stock Operator sin Validación', compute='_compute_is_vendor')

    @api.depends('user_id')
    @api.depends_context('uid')
    def _compute_is_vendor(self):
        group = self.env.ref('vendor_inventory.group_vendor')
        for record in self:
            if self.env.user.id not in group.users.ids:
                record.is_vendor  = False
            else: record.is_vendor  = True

    # @api.depends('user_id')
    # @api.depends_context('uid')
    # @api.model
    # def create(self, vals):
    #     res = super(StockPicking1, self).create(vals)
    #     group = self.env.ref('vendor_inventory.group_vendor')
    #     if self.env.user.id in group.users.ids:
    #             if res.picking_type_id.id == 1:
    #                 res.location_dest_id = self.env.user.default_warehouse_id
    #                 res.owner_id = self.env.user.partner_id
    #                 res.partner_id = self.env.user.partner_id

    def _compute_location_id(self):
        #result = super(StockPicking1, self)._compute_location_id()
        for picking in self:
            picking = picking.with_company(picking.company_id)
            if picking.picking_type_id and picking.state == 'draft':
                if picking.picking_type_id.default_location_src_id:
                    location_id = picking.picking_type_id.default_location_src_id.id
                elif picking.partner_id:
                    location_id = picking.partner_id.property_stock_supplier.id
                else:
                    _customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

                if picking.picking_type_id.default_location_dest_id:
                    location_dest_id = picking.picking_type_id.default_location_dest_id.id
                elif picking.partner_id:
                    location_dest_id = picking.partner_id.property_stock_customer.id
                else:
                    location_dest_id, _supplierloc = self.env['stock.warehouse']._get_partner_locations()

                picking.location_id = location_id
                picking.location_dest_id = location_dest_id
                if picking.picking_type_id == 1:
                    group = self.env.ref('vendor_inventory.group_vendor')
                    if self.env.user.id in group.users.ids:
                        picking.location_dest_id = self.env.user.default_warehouse_id



    @api.depends('user_id')
    @api.depends_context('uid')
    @api.model
    def default_get(self, fields):
         result = super(StockPicking1, self).default_get(fields)
         if len(result) > 1:
            if result.get('picking_type_id') == 1:
                group = self.env.ref('vendor_inventory.group_vendor')
                if self.env.user.id in group.users.ids:
                    result.update({
                        'location_dest_id': self.env.user.default_warehouse_id or False,
                        'owner_id': self.env.user.partner_id or False,
                        'partner_id': self.env.user.partner_id
                    })
         return result


# class Pickingtype(models.Model):
#     _inherit = "stock.picking.type"

#     @api.onchange('code')
#     def _onchange_picking_code(self):
#         super()._onchange_picking_code()
#         group = self.env.ref('vendor_inventory.group_vendor')
#         if self.env.user.id in group.users.ids:
#             if self.code == 'incoming':
#                 self.default_location_dest_id = self.env.user.default_warehouse_id
        