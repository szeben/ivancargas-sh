# -*- coding: utf-8 -*-
# from odoo import http


# class TraceabilityPoSoTravelWb(http.Controller):
#     @http.route('/traceability__po__so_travel__wb/traceability__po__so_travel__wb', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/traceability__po__so_travel__wb/traceability__po__so_travel__wb/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('traceability__po__so_travel__wb.listing', {
#             'root': '/traceability__po__so_travel__wb/traceability__po__so_travel__wb',
#             'objects': http.request.env['traceability__po__so_travel__wb.traceability__po__so_travel__wb'].search([]),
#         })

#     @http.route('/traceability__po__so_travel__wb/traceability__po__so_travel__wb/objects/<model("traceability__po__so_travel__wb.traceability__po__so_travel__wb"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('traceability__po__so_travel__wb.object', {
#             'object': obj
#         })
