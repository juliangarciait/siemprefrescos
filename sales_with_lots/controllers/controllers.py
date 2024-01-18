# -*- coding: utf-8 -*-
# from odoo import http


# class SalesWithLots(http.Controller):
#     @http.route('/sales_with_lots/sales_with_lots', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_with_lots/sales_with_lots/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_with_lots.listing', {
#             'root': '/sales_with_lots/sales_with_lots',
#             'objects': http.request.env['sales_with_lots.sales_with_lots'].search([]),
#         })

#     @http.route('/sales_with_lots/sales_with_lots/objects/<model("sales_with_lots.sales_with_lots"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_with_lots.object', {
#             'object': obj
#         })

