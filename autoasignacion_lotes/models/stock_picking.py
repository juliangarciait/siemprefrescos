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
        # picking_type = self.picking_type_id
        # precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # no_quantities_done = all(float_is_zero(move_line.quantity, precision_digits=precision_digits) for move_line in
        #                          self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        # no_reserved_quantities = all(
        #     float_is_zero(move_line.reserved_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
        #     self.move_line_ids)
        # if no_reserved_quantities and no_quantities_done:
        # raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if self.display_create_lot_name and self.create_lot_name:  # and not (no_reserved_quantities and no_quantities_done): # and (picking_type.use_create_lots or picking_type.use_existing_lots):
            lines_to_check = self.move_line_ids
            # if not no_quantities_done:
            lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.quantity, 0, 
                                    precision_rounding=line.product_uom_id.rounding))
            next_number = self.env['ir.sequence'].next_by_code(
                'production.lot.%s.sequence' % self.partner_id.lot_code_prefix.lower()) 
            self.purchase_id.lot = "{}{}".format(self.partner_id.lot_code_prefix, next_number)
            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        lot_name = self.get_next_lot_name(line.product_id, line.picking_id, next_number)
                        # Ensure Tag Tax Lot Ids
                        tag_lot_ids = self.get_lot_tag(line.product_id, line.picking_id, next_number)
                        lot = self.env['stock.lot'].create(
                            {'name': lot_name, 'product_id': line.product_id.id,
                             'company_id': line.move_id.company_id.id,
                             'analytic_tag_ids': tag_lot_ids,
                             }
                        )
                        line.write({'lot_name': lot.name, 'lot_id': lot.id})
                        purchase_lot1 = line.move_id.purchase_line_id
                        purchase_lot1.write({'purchase_lot': lot.id})
                
        return super().button_validate()
    
    def get_lot_tag(self, product_id, picking_id, next_number):
        # Tag Lot
        tag_lot = '%s%s' % (picking_id.partner_id.lot_code_prefix,
                            next_number)
        account_tag_lot = self.env['account.analytic.account'].search([('name', '=', tag_lot)], limit=1)
        if not account_tag_lot:
            account_tag_lot = self.env['account.analytic.account'].sudo().create({'company_id': 1, 'name': tag_lot,'active': True, 'partner_id': False, 'plan_id': 6})

        # Tag Product
        if not product_id.product_tmpl_id.account_tag_id:
            tag_product = 'P' + product_id.product_tmpl_id.lot_code_prefix
            product_tag_lot = self.env['account.analytic.account'].search([('name', '=', tag_product)], limit=1)
            if not product_tag_lot:
                product_tag_lot = self.env['account.analytic.account'].sudo().create({'name': tag_product, 'company_id': 1,'active': True, 'partner_id': False, 'plan_id': 4 })
        else:
            product_tag_lot = product_id.product_tmpl_id.account_tag_id

        # Tag Supplier
        tag_supplier = picking_id.partner_id.lot_code_prefix
        supplier_tag_lot = self.env['account.analytic.account'].search([('name', '=', tag_supplier)], limit=1)
        if not supplier_tag_lot:
            supplier_tag_lot = self.env['account.analytic.account'].sudo().create({'name': tag_supplier, 'company_id': 1,'active': True, 'partner_id': False, 'plan_id': 5 })

        return [(6, 0, [account_tag_lot.id, product_tag_lot.id, supplier_tag_lot.id])]
    
    
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