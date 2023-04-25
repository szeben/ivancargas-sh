# -*- coding: utf-8 -*-
# from odoo import http


# class PrimerModulo(http.Controller):
#     @http.route('/primer_modulo/primer_modulo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/primer_modulo/primer_modulo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('primer_modulo.listing', {
#             'root': '/primer_modulo/primer_modulo',
#             'objects': http.request.env['primer_modulo.primer_modulo'].search([]),
#         })

#     @http.route('/primer_modulo/primer_modulo/objects/<model("primer_modulo.primer_modulo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('primer_modulo.object', {
#             'object': obj
#         })
