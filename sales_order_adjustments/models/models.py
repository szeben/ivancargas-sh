# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_product_uom_qty = fields.Float(
        "Total Pedido", compute='_compute_total_product_uom_qty', store=True)
    total_qty_delivered = fields.Float(
        "Total Entregado", compute='_compute_total_qty_delivered', store=True)
    total_qty_invoiced = fields.Float(
        "Total Facturado", compute='_compute_total_qty_invoiced', store=True)
    total_qty_to_invoiced = fields.Float(
        "Total a Facturar", compute='_compute_total_qty_to_invoiced', store=True)

    @api.depends("order_line", "order_line.product_uom_qty")
    def _compute_total_product_uom_qty(self):
        for order in self:
            if order.order_line:
                order.total_product_uom_qty = sum(
                    [line.product_uom_qty for line in order.order_line])

    @api.depends("order_line", "order_line.qty_delivered")
    def _compute_total_qty_delivered(self):
        for order in self:
            if order.order_line:
                order.total_qty_delivered = sum(
                    [line.qty_delivered for line in order.order_line])

    @api.depends("order_line", "order_line.qty_invoiced")
    def _compute_total_qty_invoiced(self):
        for order in self:
            if order.order_line:
                order.total_qty_invoiced = sum(
                    [line.qty_invoiced for line in order.order_line])

    @api.depends("order_line", "order_line.qty_to_invoice")
    def _compute_total_qty_to_invoiced(self):
        for order in self:
            if order.order_line:
                order.total_qty_to_invoiced = sum(
                    [line.qty_to_invoice for line in order.order_line])


class TransportEntry(models.Model):
    _inherit = "transport.entry"

    total_qty_to_invoiced = fields.Float(
        related='picking_id.sale_id.total_qty_to_invoiced', string='Total a facturar')
