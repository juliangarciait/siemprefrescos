{
    'name': 'Product Variant Conversion',
    'version': '1.0',
    'summary': 'Manage product variant conversions',
    'description': 'Allows conversion between product variants with inventory adjustments and sale order integration.',
    'category': 'Inventory',
    'author': 'Tu Nombre',
    'depends': ['stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',  # Asegúrate de crear este archivo
        'views/product_variant_conversion_views.xml',
        'views/product_variant_conversion_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
