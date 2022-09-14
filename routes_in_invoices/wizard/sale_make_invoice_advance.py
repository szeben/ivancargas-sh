# -*- coding: utf-8 -*-

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
        so_values = super()._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
        so_values["order_route"] = order.order_route
        return so_values
