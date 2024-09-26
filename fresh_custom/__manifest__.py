{
    'name': 'Fresh Custom',
    'category': 'Uncategorized',
    'version': '0.1',
    'summary': 'Fresh Custom',
    'description': '',
    "author": 'Ernesto García Medina',
    'sequence': 1,
    "email": 'ernesto.r.2.em@gmail.com',
    "website": '',
    'depends': ['vendor_inventory', 'stock_available'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/base_security.xml',
        'views/stock_picking_views.xml',
        'views/stock_quant_views.xml',
        'views/res_partner_views.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}