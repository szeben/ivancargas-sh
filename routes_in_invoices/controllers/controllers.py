# -*- coding: utf-8 -*-
# from odoo import http


# class RoutesInInvoices(http.Controller):
#     @http.route('/routes_in_invoices/routes_in_invoices', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/routes_in_invoices/routes_in_invoices/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('routes_in_invoices.listing', {
#             'root': '/routes_in_invoices/routes_in_invoices',
#             'objects': http.request.env['routes_in_invoices.routes_in_invoices'].search([]),
#         })

#     @http.route('/routes_in_invoices/routes_in_invoices/objects/<model("routes_in_invoices.routes_in_invoices"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('routes_in_invoices.object', {
#             'object': obj
#         })
