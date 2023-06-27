from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
import re

_logger = logging.getLogger(__name__)


class QuantProductRepackWizard(models.TransientModel):
    _name = 'quant.product.repack.wizard'
    _description = 'Repack Process by Product'

    product_id = fields.Many2one('product.product', string="Initial Product")
    location_id = fields.Many2one('stock.location', string="Location")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    initial_qty = fields.Float(string="Cantidad Inicial")
    main_qty = fields.Float(string="Restante en Original")
    lines_ids = fields.One2many('quant.product.repack.lines.wizard',
                                'quant_lot_repack_id',
                                string="Repack Lines")


    scrap_qty = fields.Float(string="Cantidad desperdicio")


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.lot_id = False
            self.location_id = False
            self.lines_ids = False
            self.initial_qty = 0
            self.main_qty = 0
         
        else: 
            self.lot_id = False
            self.location_id = False
            self.lines_ids = False
            self.initial_qty = 0
            self.main_qty = 0
         
            
    @api.onchange('location_id')
    def _onchange_location_id(self):
            if self.location_id:
                self.lot_id = False
                self.lines_ids = False
                self.initial_qty = 0
                self.main_qty = 0
         
            else: 
                self.lot_id = False
                self.lines_ids = False
                self.initial_qty = 0
                self.main_qty = 0
         
        
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            val = [(0, 0, {'product_ref': variant.id,'lot_ref': self.lot_id.name, 'qty': 0.0, 'quant_lot_repack_id': self.id})
                       for variant in self.product_id.product_fabricacion.product_variant_ids]
            self.write({'lines_ids': val})
            self.initial_qty = self.lot_id.product_qty
            self.main_qty = self.lot_id.product_qty
        else:
            self.lines_ids = False
            self.initial_qty = 0
            self.main_qty = 0
            
    def _get_sum_qty_lines(self):
        return sum([line.qty for line in self.lines_ids])

    def _check_valid_quantity(self):
        if self._get_sum_qty_lines() + self.scrap_qty > self.initial_qty:
            raise UserError('Invalid Quantity, Please Fix it !')
        
        
    @api.onchange('lines_ids', 'scrap_qty')
    def _onchange_lines_ids(self):
        self._check_valid_quantity()
        self.main_qty = self.initial_qty - self.scrap_qty
        self.main_qty -= self._get_sum_qty_lines()
        
        
    def get_or_creat_lot(self, vals):
        sql = """select id, name 
                    from stock_lot 
                    where name=%(name)s AND product_id = %(product_id)s"""
        self.env.cr.execute(sql, vals)
        result = self.env.cr.dictfetchone()
        if result:
            return result.get('id')
        #self.env['stock.lot'].sudo().create(vals).id
        return 0

    def get_lot_child_quantity(self, lot_ref):
        for lot in self.lines_ids:
            if lot.lot_ref == lot_ref:
                return lot.qty
        return 0.0
    
    
    def _update_scrap_qty(self, sequence):
        StockScrap = self.env['stock.scrap']
        if self.scrap_qty > 0:
            # Create Scrap
            ss = StockScrap.sudo().create({
                'product_id': self.product_id.id,
                'scrap_qty': self.scrap_qty,
                'lot_id': self.lot_id.id,
                'location_id': self.location_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                #'origin': 'WZRPACK{}'.format(self.lot_id.id)
                'origin': 'Repack {}'.format(sequence)
            })

            ss.sudo().action_validate()
        
        
    def process_repack(self):
        _logger.info("Repack!!!")
        # _logger.info(self._get_sum_qty_lines())
        for item in self.lines_ids:
            _logger.info(item.qty)
        if self._get_sum_qty_lines() <= 0:
            raise UserError('Quantity in repack lots cannot be 0, Please Fix it !')
        sequence = self.env['ir.sequence'].next_by_code('repack') or _('New')

        self._check_valid_quantity()
        # Scrap Qty
        self._update_scrap_qty(sequence=sequence)
        # Create Inventory Adjust
        # vals = {
        #     'name': 'Repacker_Assistance v %s' % (str(self.id)),
        #     'product_ids': [(4, self.product_id.id)],
        #     'location_ids': [(4, self.location_id.id)],
        # }
        # si = self.env['stock.inventory'].sudo().create(vals)
        # si.sudo().action_start()
        # Create Lots
        lot_childs = []
        for item in self.lines_ids:
            if item.qty > 0:
                vals = {'name': item.lot_ref,
                                        'product_id': item.product_ref.id,
                                        'company_id': self.location_id.company_id.id,
                                        'parent_lod_id': self.lot_id.id,
                                        #'analytic_tag_ids': [(4, tag.id) for tag in self.lot_id.analytic_tag_ids], checar despues
                                        }
                lote = self.get_or_creat_lot(vals)
                if lote == 0:
                    nuevo_lote = self.env['stock.lot'].sudo().create(vals).id
                    nuevo_quant = [{'product_id': item.product_ref.id, 'location_id': self.location_id.id, 'quantity': 0, 'lot_id': nuevo_lote}]
                    nuevo_quant = self.env['stock.quant'].sudo().create(nuevo_quant)
                    self.env['stock.quant'].with_context(inventory_name='Repack {}'.format(sequence), inventory_mode=False).create({
                                    'product_id': item.product_ref.id,
                                    'location_id': self.location_id.id,
                                    'inventory_quantity': item.qty,
                                    'lot_id': nuevo_lote,
                                        })._apply_inventory()
                    #crear lote
                else:
                    #old_qty = self.env['stock.lot'].browse(lote).product_qty
                    #new_qty = old_qty + item.qty
                    self.env['stock.quant'].with_context(inventory_name='Repack {}'.format(sequence), inventory_mode=False).create({
                                    'product_id': item.product_ref.id,
                                    'location_id': self.location_id.id,
                                    'inventory_quantity': item.qty,
                                    'lot_id': lote,
                                        })._apply_inventory()
        #actualizar original
        cantidad_nueva = 0 - self._get_sum_qty_lines()  
        self.env['stock.quant'].with_context(inventory_name='Repack {}'.format(sequence), inventory_mode=False).create({
                                    'product_id': self.product_id.id,
                                    'location_id': self.location_id.id,
                                    'inventory_quantity': cantidad_nueva,
                                    'lot_id': self.lot_id.id,
                                        })._apply_inventory()
                    
                
                
        # ReOrganize and Create Move Lines
        # lot_process = []
        # for line in si.line_ids:
        #     if line.prod_lot_id.id == self.lot_id.id:
        #         line.product_qty = self.final_qty
        #     if (line.prod_lot_id.id in lot_childs
        #             and line.prod_lot_id.id not in lot_process):
        #         lot_process.append(line.prod_lot_id.id)
        #         line.product_qty = self.get_lot_child_quantity(line.prod_lot_id.name)
        # missing_lots = [lot_id for lot_id in lot_childs if lot_id not in lot_process]
        # lot_ids = self.env['stock.production.lot'].browse(missing_lots)
        # list_line_ids = []
        # for lot_id in lot_ids:
        #     list_line_ids.append((0, 0, {
        #         'company_id': self.location_id.company_id.id,
        #         'prod_lot_id': lot_id.id,
        #         'product_id': self.product_id.id,
        #         'location_id': self.location_id.id,
        #         'product_qty': self.get_lot_child_quantity(lot_id.name)
        #     }))
        # # Check Main Lot is in SI
        # if self.final_qty > 0:
        #     ids = [line.prod_lot_id.id for line in si.line_ids]
        #     if self.lot_id.id not in ids:
        #         #Add main Lot qty
        #         list_line_ids.append((0, 0, {
        #             'company_id': self.location_id.company_id.id,
        #             'prod_lot_id': self.lot_id.id,
        #             'product_id': self.product_id.id,
        #             'location_id': self.location_id.id,
        #             'product_qty': self.final_qty
        #         }))
        # si.line_ids = list_line_ids
        # si.sudo().action_validate()
         

    
class QuantLotRepackWizard(models.TransientModel):
    _name = 'quant.product.repack.lines.wizard'
    _description = 'Repack Process by Lot'

    product_ref = fields.Many2one('product.product', string='Variedad')
    #product_ref = fields.Integer(string='Variedad')
    lot_ref = fields.Char(string="Lot")
    qty = fields.Float(string="Initial Qty")
    quant_lot_repack_id = fields.Many2one('quant.product.repack.wizard' , string="quant_lot_repack_id")


    

    # @api.onchange('product_id', 'location_id')
    # def _onchange_product_id(self):
    #      if self.product_id:
    #             self.lot_ids = "[('product_id', '=', {})]".format(self.product_id.id)
    #      else:
    #             selflot_ids = False
        # domain = [('lot_id', '!=', False), ('quantity', '>', 0)]
        # if self.product_id:
        #     domain += [('product_id', '=', self.product_id.id)]
        # if self.location_id:
        #     domain += [('location_id', '=', self.location_id.id)]
        # lot_ids = [qt.lot_id.id for qt in self.env['stock.quant'].search(domain)]
        # variant_ids = [pp.id for pp in self.product_id.product_variant_ids if pp != self.product_id]
        # self.lot_id = False
        # #return {'domain': {'lot_id': [('id', 'in', lot_ids)],
        # #                   'product_dest_id': [('id', 'in', variant_ids)]}}
        # lotes = self.env['stock.lot'].search([('id', 'in', lot_ids)])
        # self.lot_id = lotes
        # self.product_dest_id = variant_ids
