# -*- coding: utf-8 -*-

{
    'name' : "facturacion electronica mexicana custom odoo 16",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Julian Garcia", 
    'website' : "",
    'category' : "Inventory",
    'depends' : [
        'account',
        'sale',
        'base'
    ],
    'data' : [
        'views/report_invoice.xml',
        'views/res_partner.xml'

    ],
}