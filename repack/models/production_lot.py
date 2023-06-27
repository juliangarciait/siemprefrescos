from odoo import api, fields, models


class LotData(models.Model):
    _inherit = 'stock.lot'

    """ analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags',
        help="This field contains the information related to the account tags for this lot",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]") """

    parent_lod_id = fields.Many2one('stock.lot', string='Parent Lot',
                                    help="This field contains the information related to the Parent Lot if"
                                         "it is repack lot")

    child_lot_ids = fields.One2many('stock.lot', 'parent_lod_id',
                                    string="Child Lots")

    type_lot = fields.Selection(
        string='Type',
        selection=[('product_repack', 'Product Repack'),
                   ('lot_repack', 'Lot Repack'), ],
    )

    product_qty_store = fields.Float('Quantity_store', compute='_product_qty_store', store=True)

    @api.depends('product_qty')
    def _product_qty_store(self):
        for lot in self:
            lot.product_qty_store = lot.product_qty

    # lot_tag = fields.Many2one('stock.lot.tag',string='Etiqueta')

    # def name_get(self):
    #     res = []
    #     for record in self:
    #         lot_tag_name = ''
    #         if record.lot_tag.name:
    #             lot_tag_name = ' - '+record.lot_tag.name
    #         res.append((record.id,record.name+'{}'.format(lot_tag_name)))
    #     return res