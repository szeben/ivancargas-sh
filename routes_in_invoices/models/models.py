# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_route = fields.Many2one(
        comodel_name="transport.route",
        string="Ruta",
    )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res["order_route"] = self.order_route
        return res


class PurchaseLine(models.Model):
    _inherit = 'purchase.order.line'

    order_route = fields.Many2one(
        comodel_name="transport.route",
        string="Ruta",
    )

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res["order_route"] = self.order_route
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    order_route = fields.Many2one(
        comodel_name="transport.route",
        string="Ruta",
    )
