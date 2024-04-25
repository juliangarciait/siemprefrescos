# -*- coding: utf-8 -*-
# from odoo import http


# class MultipleInvoiceSlips(http.Controller):
#     @http.route('/multiple_invoice_slips/multiple_invoice_slips/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/multiple_invoice_slips/multiple_invoice_slips/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('multiple_invoice_slips.listing', {
#             'root': '/multiple_invoice_slips/multiple_invoice_slips',
#             'objects': http.request.env['multiple_invoice_slips.multiple_invoice_slips'].search([]),
#         })

#     @http.route('/multiple_invoice_slips/multiple_invoice_slips/objects/<model("multiple_invoice_slips.multiple_invoice_slips"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('multiple_invoice_slips.object', {
#             'object': obj
#         })
