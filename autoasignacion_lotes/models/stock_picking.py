# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
from itertools import groupby
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    create_lot_name = fields.Boolean('Create Lot Names', default=True)
    display_create_lot_name = fields.Boolean(compute='_compute_display_create_lot_name')


    @api.depends('state', 'picking_type_id',
                 'partner_id.sequence_id', 'partner_id.lot_code_prefix', 'location_dest_id')
    def _compute_display_create_lot_name(self):
        for picking in self:
            picking.display_create_lot_name = (
                # picking.partner_id.sequence_id and
                # picking.partner_id.lot_code_prefix and
                    picking.picking_type_id.code == 'incoming' and
                    picking.state not in ('done', 'cancel')
            )


    def button_validate(self):
        """ Si es necesario crea lotes """
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                                 self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(
            float_is_zero(move_line.reserved_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        # if no_reserved_quantities and no_quantities_done:
        # raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if self.display_create_lot_name and self.create_lot_name:  # and not (no_reserved_quantities and no_quantities_done): # and (picking_type.use_create_lots or picking_type.use_existing_lots):
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )
            next_number = self.env['ir.sequence'].next_by_code(
                'production.lot.%s.sequence' % self.partner_id.lot_code_prefix.lower()) 
            self.purchase_id.lot = "{}{}".format(self.partner_id.lot_code_prefix, next_number)
            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        lot_name = self.get_next_lot_name(line.product_id, line.picking_id, next_number)
                        # Ensure Tag Tax Lot Ids
                        #tax_tag_lot_ids = self.get_lot_tax_tag(line.product_id, line.picking_id, next_number)
                        lot = self.env['stock.lot'].create(
                            {'name': lot_name, 'product_id': line.product_id.id,
                             'company_id': line.move_id.company_id.id,
                             #'analytic_tag_ids': tax_tag_lot_ids,
                             }
                        )
                        line.write({'lot_name': lot.name, 'lot_id': lot.id})
                        purchase_lot1 = line.move_id.purchase_line_id
                        purchase_lot1.write({'purchase_lot': lot.id})
                
        #         if lot and not lot.analytic_tag_ids:
        #             raise UserError("The lot with number %s don't have analytic tags" % (lot.name))
               
        # so_id = self.sale_id

        # # Check lot Traceability
        # self.action_fix_order_with_move_lines()
        return super().button_validate()
    
    
    def get_next_lot_name(self, product_id, picking_id, next_number):
        """ Method called by button "Create Lot Numbers", it automatically
            generates Lot names based on:
            - product.template.lot_code_prefix: 2 integers
            - res.partner.lot_code_prefix: 3 letters
            - Two digits Year
            - One dash "-"
            - res.partner.sequence.id: 4 integers sequence
            - product.product.variant: 2-3 chrs
            
            Samples: 02LMX20-0001#230
                     02FDP20-0016#230 """
        if not product_id.product_tmpl_id.lot_code_prefix:
            raise UserError('Enter Product [%s] Lot Code and try again!.' % product_id.name)
        if not picking_id.partner_id.lot_code_prefix:
            raise UserError('Enter Vendor [%s] Lot Code and try again!.' % picking_id.partner_id.name)
        if not picking_id.partner_id.sequence_id:
            raise UserError('Assing a sequence to Vendor [%s] and try again!.' % picking_id.partner_id.name)
        # next_number = self.env['ir.sequence'].next_by_code('production.lot.%s.sequence' % picking_id.partner_id.lot_code_prefix.lower())
        # se remueve anterior ya que aumenta contador cuando se piden varios articulos juntos
        if len(product_id.product_template_attribute_value_ids) == 0:
            return '%s%s%s' % (product_id.product_tmpl_id.lot_code_prefix,
                               picking_id.partner_id.lot_code_prefix,
                               next_number)
        else:
            try:  # revisa si la variante es numero y agrega simbolo antes del numero
                attribute = int(product_id.product_template_attribute_value_ids[0].product_attribute_value_id.name)
                attribute = '#%s' % (str(attribute))
            except ValueError:
                attribute = product_id.product_template_attribute_value_ids[0].product_attribute_value_id.name
            return '%s%s%s%s' % (product_id.product_tmpl_id.lot_code_prefix,
                                 picking_id.partner_id.lot_code_prefix,
                                 next_number,
                                 attribute)

    # def action_fix_order_with_move_lines(self):
    #     _logger.info("Action")
    #     if self.picking_type_id.code == 'outgoing' and self.sale_id:
    #         try:
    #             if self.search_inconsistencies_with_so():
    #                 _logger.info('There are inconsistencies')
    #                 self.sync_moves_with_sale_order()
    #             else:
    #                 _logger.info('The order is correct in relation to the move lines')
    #         except Exception as e:
    #             raise UserError(_("Please check the following: %s" % str(e)))
    #     else:
    #         _logger.info("No is outgoing picking or there is not sale_id")

    # def action_fix_quants_un_reserved(self, last_days=''):
    #     domain = []
    #     if last_days != '':
    #         expiration_date = datetime.now() - timedelta(days=int(last_days))
    #         domain = [('create_date', '>=', expiration_date.strftime("%Y-%m-%d"))]
    #     quants = self.env["stock.quant"].search(domain)
    #     move_line_ids = []
    #     warning = ""
    #     for quant in quants:
    #         move_lines = self.env["stock.move.line"].search(
    #             [
    #                 ("product_id", "=", quant.product_id.id),
    #                 ("location_id", "=", quant.location_id.id),
    #                 ("lot_id", "=", quant.lot_id.id),
    #                 ("package_id", "=", quant.package_id.id),
    #                 ("owner_id", "=", quant.owner_id.id),
    #                 ("product_qty", "!=", 0),
    #             ]
    #         )
    #         move_line_ids += move_lines.ids
    #         reserved_on_move_lines = sum(move_lines.mapped("product_qty"))
    #         move_line_str = str.join(
    #             ", ", [str(move_line_id) for move_line_id in move_lines.ids]
    #         )
    #         if quant.location_id.should_bypass_reservation():
    #             # If a quant is in a location that should bypass the reservation, its `reserved_quantity` field
    #             # should be 0.
    #             if quant.reserved_quantity != 0:
    #                 quant.write({"reserved_quantity": 0})
    #         else:
    #             # If a quant is in a reservable location, its `reserved_quantity` should be exactly the sum
    #             # of the `product_qty` of all the partially_available / assigned move lines with the same
    #             # characteristics.
    #             if quant.reserved_quantity == 0:
    #                 if move_lines:
    #                     move_lines.with_context(bypass_reservation_update=True).write(
    #                         {"product_uom_qty": 0}

    #                     )
    #             elif quant.reserved_quantity < 0:
    #                 quant.write({"reserved_quantity": 0})
    #                 if move_lines:
    #                     move_lines.with_context(bypass_reservation_update=True).write(
    #                         {"product_uom_qty": 0}
    #                     )
    #             else:
    #                 if reserved_on_move_lines != quant.reserved_quantity:
    #                     move_lines.with_context(bypass_reservation_update=True).write(
    #                         {"product_uom_qty": 0}
    #                     )
    #                     quant.write({"reserved_quantity": 0})
    #                 else:
    #                     if any(move_line.product_qty < 0 for move_line in move_lines):
    #                         move_lines.with_context(bypass_reservation_update=True).write(
    #                             {"product_uom_qty": 0}
    #                         )
    #                         quant.write({"reserved_quantity": 0})
    #     move_lines = self.env["stock.move.line"].search(
    #         [
    #             ("product_id.type", "=", "product"),
    #             ("product_qty", "!=", 0),
    #             ("id", "not in", move_line_ids),
    #         ]
    #     )
    #     move_lines_to_unreserve = []
    #     for move_line in move_lines:
    #         if not move_line.location_id.should_bypass_reservation():
    #             move_lines_to_unreserve.append(move_line.id)
    #     if len(move_lines_to_unreserve) > 1:
    #         self.env.cr.execute(
    #             """ 

    #                 UPDATE stock_move_line SET product_uom_qty = 0, product_qty = 0 WHERE id in %s ;

    #             """
    #             % (tuple(move_lines_to_unreserve),)
    #         )
    #     elif len(move_lines_to_unreserve) == 1:
    #         self.env.cr.execute(
    #             """ 

    #             UPDATE stock_move_line SET product_uom_qty = 0, product_qty = 0 WHERE id = %s ;

    #             """
    #             % (move_lines_to_unreserve[0])
    #         )

    # def search_inconsistencies_with_so(self):
    #     """
    #         See if the lines of the stock move line are the same as the so
    #         If there are inconsistencies return True
    #         else return False
    #     """
    #     # First Len SO Lines and SO Moves
    #     if len(self.sale_id.order_line) != len(self.move_lines):
    #         return True
    #     # Second Lot_ID is change or Qty lot ID Change.
    #     for move_line in self.move_line_ids:
    #         line_founded = False
    #         for line in self.sale_id.order_line:
    #             if (line.lot_id == move_line.lot_id
    #                     and line.product_id == move_line.product_id
    #                     and line.product_uom_qty == move_line.qty_done):
    #                 line_founded = True
    #                 break
    #         if not line_founded:
    #             return True
    #     # All lines is correct in SO, return False
    #     return False

    # def update_empty_delivery_lines(self, list_to_recreate):
    #     for move in self.move_line_ids:
    #         if (move.qty_done == 0):
    #             for line in list_to_recreate:
    #                 if (line.get('product_id') == move.product_id.id
    #                         and line.get('lot_id') == move.lot_id.id):
    #                     move.qty_done = line.get('product_uom_qty')

    # def button_force_do_unreserve(self):
    #     """
    #         Button Action
    #         Force Unreserved
    #         Deleted all qtys reserved on move lines
    #     """
    #     for move in self.move_line_ids:
    #         if move.product_uom_qty > 0:
    #             move.update_force_unreserve_move_line()
    #     return True

    # def button_load_move_line_ids(self):
    #     """
    #         Button Action
    #         Load stock.move.lines from SO
    #         Without reserved
    #     """
    #     move_line_vals_list = []
    #     for line in self.move_line_ids:
    #         # Validate qty reserved or done
    #         if line.product_uom_qty > 0: # or line.qty_done > 0:
    #             raise UserError('The line with Product [%s] is a line with reserve o qty done, '
    #                             'for recreate lines should be empty, please you clean it!.' % line.product_id.name)
    #         if line.state in ('done', 'cancel'):
    #             raise UserError('You cannot recreate the lines with the delivery in canceled or done status. '
    #                             'Please you fix it')

    #     # Force Unlink operations ()
    #     self.move_line_ids.with_context(is_force=True).unlink()
    #     for move in self.move_lines:
    #         # Create Lines
    #         vals = move._prepare_move_line_vals()
    #         vals['lot_id'] = move.lot_id.id
    #         vals['qty_done'] = move.product_qty
    #         move_line_vals_list.append(vals)
    #     if len(move_line_vals_list) > 0:
    #         self.env['stock.move.line'].sudo().create(move_line_vals_list)
    #     return True

    # def get_default_tax_id(self):
    #     tax_id_id = False
    #     for line in self.sale_id.order_line:
    #         if line.tax_id:
    #             tax_id_id = line.tax_id.id
    #             break
    #     return tax_id_id

    # def sync_moves_with_sale_order(self):
    #     """
    #         From the moves_lines_ids
    #         The necessary stock moves are generated
    #         to separate by Lot
    #         @param: self : stock.picking ref

    #     """
    #     # Inconsistency, FIX SO.
    #     order_id_ref = self.sale_id
    #     # Get and filter move_lines_ids with qty > 0
    #     list_ids_to_recreate = list(filter(lambda line: line.get('product_uom_qty') > 0, self.get_list_new_quotation()))
    #     if len(list_ids_to_recreate) == 0:
    #         raise UserError('Nothing line has products to validate, please check it')

    #     # Force Unreserve
    #     self.button_force_do_unreserve()
    #     # Order fix
    #     order_id_ref.action_unlock()
    #     order_id_ref.action_cancel()
    #     order_id_ref.action_draft()
    #     order_id_ref.order_line.unlink()
    #     # CleanDelivery
    #     self.set_to_draft()
    #     # Secure unreserve qty
    #     self.button_force_do_unreserve()
    #     # Force Unlink operations ()
    #     self.move_lines.unlink()
    #     self.move_line_ids.with_context(is_force=True).unlink()
    #     self.write({'state': 'cancel'})
    #     _logger.info("delete order")
    #     # Set new orderlines
    #     order_id_ref.env['stock.picking'].create_sale_order_lines(order_id_ref, list_ids_to_recreate)
    #     order_id_ref.with_context(is_force=True).action_confirm()
    #     new_picking = order_id_ref.picking_ids
    #     new_picking.button_load_move_line_ids()
    #     new_picking.update_empty_delivery_lines(list_ids_to_recreate)

    # def get_custom_product_price(self, sale_id, product_id):
    #     for line in sale_id.order_line:
    #         if line.product_id.id == product_id.id:
    #             return line.price_unit
    #     # Searching other recent orders
    #     domain = [('product_id', '=', product_id.id)]
    #     line = self.env['sale.order.line'].search(domain, limit=1)
    #     if line:
    #         return line.price_unit
    #     return False

    # def get_list_new_quotation(self):
    #     list = []
    #     for lines in self.move_line_ids_without_package:
    #         vals = {
    #             'product_id': lines.product_id.id,
    #             'name': lines.product_id.name,
    #             'order_id': self.sale_id.id,
    #             'lot_id': lines.lot_id.id,
    #             'product_uom': lines.product_id.uom_id.id,
    #             'product_uom_qty': lines.qty_done
    #         }
    #         # Serching default Tax
    #         tax_id_id = self.get_default_tax_id()
    #         if tax_id_id:
    #             vals['tax_id_id'] = tax_id_id
    #         price_unit = self.get_custom_product_price(self.sale_id, lines.product_id)
    #         if price_unit:
    #             vals['price_unit'] = price_unit

    #         list.append(vals)
    #     return list

    # def create_sale_order_lines(self, sale_id, list_ids):
    #     line_env = self.env['sale.order.line']
    #     for item in list_ids:
    #         vals = {
    #             'product_id': item.get('product_id'),
    #             'name': item.get('name'),
    #             'order_id': sale_id.id,
    #             'lot_id': item.get('lot_id'),
    #             'product_uom': item.get('product_uom'),
    #             'product_uom_qty': item.get('product_uom_qty'),
    #         }
    #         if item.get('tax_id_id'):
    #             vals['tax_id']: [[6, False, [int(item.get('tax_id_id'))]]]
    #         if item.get('price_unit'):
    #             vals['price_unit'] = item.get('price_unit')
    #         line_env.sudo().create([vals])
    #     # update_sale_oder
    #     for line in sale_id.order_line:
    #         if line.lot_available_sell == 0 and line.product_uom_qty != 0:
    #             lot_id = line.lot_id
    #             qty = line.product_uom_qty
    #             price_unit = line.price_unit
    #             line.product_id_change()  # Calling an onchange method to update the
    #             line.lot_id = lot_id
    #             line._onchange_lot_id()
    #             line._onchange_lot_sel_account()
    #             line.product_uom_qty = qty
    #             line.price_unit = price_unit
    #             # if not tax_id:
    #             #    line.tax_id = False

    # def create_sale_order_line_from_line_move(self, line_by_lot):
    #     """
    #         Create new sale.order.line associated
    #         to sale_id
    #         @param: self : stock.picking ref
    #         @param: line_by_lot : stock.move.line
    #     """
    #     line_env = self.env['sale.order.line']
    #     self.sale_id.sudo().write({'state': 'sale'})
    #     vals = {
    #         'product_id': line_by_lot.product_id.id,
    #         'name': line_by_lot.product_id.name,
    #         'order_id': self.sale_id.id,
    #         'lot_id': line_by_lot.lot_id.id,
    #         'product_uom': line_by_lot.product_id.uom_id.id}
    #     new_line = line_env.create([vals])
    #     self.sale_id.sudo().write({'state': 'done'})
    #     # Calling an onchange method to update the record
    #     new_line.product_id_change()
    #     return new_line

    # @api.depends('state')
    # def _compute_sync_with_state(self):
    #     for stock in self:
    #         originally_states = list(dict(stock._fields['state'].selection).keys())
    #         if not stock.custom_state_delivery:
    #             _logger.info('Custom state was set')
    #             stock.custom_state_delivery = stock.state
    #         elif stock.custom_state_delivery in originally_states:
    #             stock.custom_state_delivery = stock.state
    #             _logger.info('Custom state was set')
    #         else:
    #             _logger.info('Custom state was not set')

    # @api.onchange('move_line_ids')
    # def onchange_move_line_ids(self):
    #     list_mapped = []
    #     for line in self.move_line_ids:
    #         if (line.product_id, line.lot_id) in list_mapped:
    #             raise UserError('Product {} with Lot {}! Already exist on the Operations Lines. Please add amount in '
    #                             'existing Operation line'.format(
    #                 str(line.product_id.name), line.lot_id.name))
    #         list_mapped.append((line.product_id, line.lot_id))

    # @api.onchange('move_line_ids_without_package')
    # def onchange_move_line_ids_without_package(self):
    #     list_mapped = []
    #     for line in self.move_line_ids_without_package:
    #         if (line.product_id, line.lot_id) in list_mapped:
    #             raise UserError('Product {} with Lot {}! Already exist on the Operations Lines. Please add amount in '
    #                             'existing Operation line'.format(
    #                 str(line.product_id.name), line.lot_id.name))
    #         list_mapped.append((line.product_id, line.lot_id))

    # @api.onchange('move_line_nosuggest_ids')
    # def onchange_nosuggest_ids(self):
    #     list_mapped = []
    #     for line in self.move_line_nosuggest_ids:
    #         if (line.product_id, line.lot_id) in list_mapped:
    #             raise UserError('Product {} with Lot {}! Already exist on the Operations Lines. Please add amount in '
    #                             'existing Operation line'.format(
    #                 str(line.product_id.name), line.lot_id.name))
    #         list_mapped.append((line.product_id, line.lot_id))

    # def create_stock_move_from_line_move(self, line_by_lot, sale_order_line):
    #     """
    #         Create new stock.move associated
    #         to stock.picking and sale.order.line
    #         @param: self : stock.picking ref
    #         @param: line_by_lot : stock.move.line
    #     """
    #     return self.env['stock.move'].create({
    #         'name': line_by_lot.product_id.name,
    #         'product_id': line_by_lot.product_id.id,
    #         'product_uom_qty': line_by_lot.qty_done,
    #         'product_uom': line_by_lot.product_uom_id.id,
    #         'picking_id': line_by_lot.picking_id.id,
    #         'location_id': line_by_lot.location.id.id,
    #         'location_dest_id': line_by_lot.location_dest_id.id,
    #         'sale_line_id': sale_order_line.id
    #     })

    # def get_lot_tax_tag(self, product_id, picking_id, next_number):
    #     # Tag Lot
    #     tag_lot = '%s%s' % (picking_id.partner_id.lot_code_prefix,
    #                         next_number)
    #     account_tag_lot = self.env['account.analytic.tag'].search([('name', '=', tag_lot)], limit=1)
    #     if not account_tag_lot:
    #         account_tag_lot = self.env['account.analytic.tag'].sudo().create({'name': tag_lot})

    #     # Tag Product
    #     if not product_id.product_tmpl_id.account_tag_id:
    #         tag_product = product_id.product_tmpl_id.lot_code_prefix
    #         product_tag_lot = self.env['account.analytic.tag'].search([('name', '=', tag_product)], limit=1)
    #         if not product_tag_lot:
    #             product_tag_lot = self.env['account.analytic.tag'].sudo().create({'name': tag_product})
    #     else:
    #         product_tag_lot = product_id.product_tmpl_id.account_tag_id

    #     # Tag Supplier
    #     tag_supplier = picking_id.partner_id.lot_code_prefix
    #     supplier_tag_lot = self.env['account.analytic.tag'].search([('name', '=', tag_supplier)], limit=1)
    #     if not supplier_tag_lot:
    #         supplier_tag_lot = self.env['account.analytic.tag'].sudo().create({'name': tag_supplier})

    #     return [(6, 0, [account_tag_lot.id, product_tag_lot.id, supplier_tag_lot.id])]




class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Crate", copy=False)

    @api.model
    def create(self, vals):
        if vals.get('sale_line_id'):
            sale_line_id = self.env['sale.order.line'].browse(vals['sale_line_id'])
            if sale_line_id and sale_line_id.lot_id:
                vals.update({'lot_id': sale_line_id.lot_id.id})
        return super(StockMove, self).create(vals)

    # def write(self,vals):
    # res = super(StockMove, self).write(vals)
    # for rec in self:
    # if rec.sale_line_id and rec.picking_id and rec.lot_id and rec.move_line_ids and sum(rec.move_line_ids.mapped('qty_done')) == 0.0:
    # for line in rec.move_line_ids:
    # line.lot_id = rec.lot_id.id
    # line.qty_done = line.product_uom_qty #rec.product_uom_qty
    # return res

    # def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
    #     result = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
    #     tags_ids = []
    #     if self.scrapped or self.inventory_id:
    #         for move in self.move_line_ids:
    #             if move.lot_id and move.lot_id.analytic_tag_ids:
    #                 for tag in move.lot_id.analytic_tag_ids:
    #                     tags_ids.append(tag.id)
    #         for line in result:
    #             result[line].update({'analytic_tag_ids': tags_ids})
    #     return result

    # def _update_reserved_quantity(
    #         self,
    #         need,
    #         available_quantity,
    #         location_id,
    #         lot_id=None,
    #         package_id=None,
    #         owner_id=None,
    #         strict=True,
    # ):
    #     if self.sale_line_id and self.sale_line_id.lot_id and self.product_id and self.product_id.tracking == 'lot':
    #         lot_id = self.sale_line_id.lot_id

    #     return super()._update_reserved_quantity(
    #         need,
    #         available_quantity,
    #         location_id,
    #         lot_id=lot_id,
    #         package_id=package_id,
    #         owner_id=owner_id,
    #         strict=strict,
    #     )

    # def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
    #     vals = super()._prepare_move_line_vals(
    #         quantity=quantity, reserved_quant=reserved_quant
    #     )
    #     if reserved_quant and self.sale_line_id:
    #         vals["lot_id"] = self.sale_line_id.lot_id.id
    #     return vals
