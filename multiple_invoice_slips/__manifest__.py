# -*- coding: utf-8 -*-
{
    'name': "Print Multiple Copies of Invoice",

    'summary': """
       This odoo app helps to print multiple copies of invoice with your desired text.""",

    'description': """
        This odoo app helps to print multiple copies of invoice.
    """,

    "author": "Cybat",
    "website": "https://www.cybat.net",
    "price": 10.00,
    "currency": 'EUR',
    'version': '14.0.0.1',
    'depends': ['account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/inherited_external_layout.xml',
        'views/templates.xml',
        'views/invoice_slip.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'application': True,
}
