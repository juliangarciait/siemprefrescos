# -*- coding: utf-8 -*-

{
    'name' : "Actualizacion de valuacion",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'stock',
        'purchase',
        'sales_lot'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/purchase.xml',
        'views/stock_lot.xml'
    ],
}