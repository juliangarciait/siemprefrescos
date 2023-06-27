# -*- coding: utf-8 -*-

{
    'name' : "repack odoo 16",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'stock',
        'product'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'wizard/quant_product_repack_view.xml',
        'views/product_template.xml'

    ],
}