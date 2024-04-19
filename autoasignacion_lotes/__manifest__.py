# -*- coding: utf-8 -*-

{
    'name' : "auto asignacion de lotes odoo 16",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'purchase',
        'product',
        'sale'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/product_template.xml',
        'views/stock_picking.xml',
        'views/purchase_order.xml',
        'views/stock_lot.xml',
        'wizard/partner_secuence_change.xml'

    ],
}