from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
from itertools import groupby
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"


    def button_load_move_line_ids(self):
        """
            Button Action
            Load stock.move.lines from SO
            Without reserved
        """
        move_line_vals_list = []
        for line in self.move_line_ids:
            # Validate qty reserved or done
            if line.product_uom_qty > 0: # or line.qty_done > 0:
                raise UserError('The line with Product [%s] is a line with reserve o qty done, '
                                'for recreate lines should be empty, please you clean it!.' % line.product_id.name)
            if line.state in ('done', 'cancel'):
                raise UserError('You cannot recreate the lines with the delivery in canceled or done status. '
                                'Please you fix it')

        # Force Unlink operations ()
        self.move_line_ids.with_context(is_force=True).unlink()
        for move in self.move_ids:
            # Create Lines
            vals = move._prepare_move_line_vals()
            vals['lot_id'] = move.lot_id.id
            vals['qty_done'] = move.product_qty
            move_line_vals_list.append(vals)
        if len(move_line_vals_list) > 0:
            self.env['stock.move.line'].sudo().create(move_line_vals_list)
        return True
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Create", copy=False)

    @api.model
    def create(self, vals):
        if vals.get('sale_line_id'):
            sale_line_id = self.env['sale.order.line'].browse(vals['sale_line_id'])
            if sale_line_id and sale_line_id.lot_id:
                vals.update({'lot_id': sale_line_id.lot_id.id})
        return super(StockMove, self).create(vals)


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

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if reserved_quant and self.sale_line_id:
            vals["lot_id"] = self.sale_line_id.lot_id.id
        return vals


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Onchange_lod_id
        """
        #if self.picking_id and self.product_uom_qty > 0 and self.lot_id:
        #    self.update_force_unreserve_move_line()
        pass

    def update_force_unreserve_move_line(self):
        """
          Update reserve quants if lot_id is changed!!!
          @param: is_force: True if is inmediatally Change on press (Force Unreserved Button)
                            False if is onchange_method (Commit on save)
        """
        if self.picking_id.state not in ('done', 'cancel'):
            self.product_uom_qty = 0