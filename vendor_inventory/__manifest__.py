# -*- coding: utf-8 -*-

{
    'name' : "Inventario para vendors",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'stock'
    ],
    'data' : [
        'security/groups.xml',
        'views/stock_picking.xml',
        'views/res_user.xml'
    ],
}