# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class tax_withholdings(models.Model):
#     _name = 'tax_withholdings.tax_withholdings'
#     _description = 'tax_withholdings.tax_withholdings'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
