# -*- coding: utf-8 -*-

{
    'name' : "Sales with lot",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'stock',
        'product',
        'sale'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/sales.xml'

    ],
}