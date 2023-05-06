# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from itertools import groupby
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockPickingInherit(models.Model):

    _inherit = 'stock.picking'

    purchase_order = fields.Many2one(
        comodel_name='purchase.order', string='Pedido de Compra')

    product_id_related = fields.Many2many(
        related='sale_id.x_studio_many2many_field_BoBwj')

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        for a in self:
            entry = self.env['transport.entry'].search(
                [('picking_id', '=', a.id)])
            if not entry:
                self.env['transport.entry'].create({
                    'date': date.today(),
                    'active': True,
                    'picking_id': a.id,
                    'lr_number': a.lr_number,
                    'customer_id': a.partner_id.id,
                    'contact_person': a.transport_id.contact_name,
                    'no_of_parcels': a.no_of_parcels,
                    'transport_id': a.transport_id.id,
                    'tag_ids': a.vehicle_id.id,
                    'date': a.date,
                    'driver_id': a.driver_id.id,
                    'sale_order': a.origin,
                    'location_dest_id': a.location_dest_id.id,
                })

        value = []
        for location in self.transport_routes_ids:
            value.append([0, 0, {'source_loc': location.source_loc.id,
                                 'dest_loc': location.dest_loc.id,
                                 'distance': location.distance,
                                 'time': location.time,
                                 'note': location.note,
                                 'tracking_number': self.tracking_number,
                                 }])
        res = self.env['transport.entry'].search(
            [('picking_id', '=', self.id)])

        if not res.transport_rote_ids:
            res.write({
                'lr_number': self.lr_number,
                'transport_rote_ids': value,
            })

        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits)
                                     for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(
                move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(
                        line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') %
                                ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(
                    pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
                    pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
                    ', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Para escribir el x_studio_wbgua en la orden de compra

        purchase_obj = self.env['purchase.order'].sudo()
        po_obj = purchase_obj.search([('id', '=', self.purchase_order.id)])

        if (po_obj):
            po_wbgua_anterior = po_obj.wbgua

            if (po_wbgua_anterior):
                po_obj.write(
                    {'wbgua': f"{po_obj.wbgua} / {self.x_studio_wbgua}"})

                body = f"Wb/guía: {po_wbgua_anterior} ---> {po_obj.wbgua}"
                po_obj.message_post(body=body)
            else:
                po_obj.write({'wbgua': self.x_studio_wbgua})

                body = f"Wb/guía: {po_obj.wbgua}"
                po_obj.message_post(body=body)

        if (self.x_studio_operacion_transporte):
            # Para escribir el x_studio_wbgua en la orden de venta
            sale_obj = self.env['sale.order'].sudo()
            so_obj = sale_obj.search([('id', '=', self.sale_id.id)])
            if (so_obj):

                if (so_obj.wbgua):
                    so_obj.write(
                        {'wbgua': f"{so_obj.wbgua} / {self.x_studio_wbgua}"})
                else:
                    so_obj.write({'wbgua': self.x_studio_wbgua})

            # Para escribir el x_studio_wbgua en las lineas de orden de venta de acuerdo a los move_line del stock move
            if (self.move_lines):

                for move_line in self.move_lines:

                    sale_line_id = move_line.sale_line_id

                    sale_line_obj = self.env['sale.order.line'].sudo()

                    sale_line = sale_line_obj.search(
                        [('id', '=', sale_line_id.id)])

                    if (sale_line):
                        order_line = self.env['sale.order'].sudo()
                        order_line_obj = order_line.search(
                            [('order_line', '=', sale_line_id.id)])

                        sl_wbgua_anterior = sale_line.wbgua

                        if (move_line.quantity_done > 0):

                            if (sl_wbgua_anterior):

                                sale_line.write(
                                    {'wbgua': f"{sale_line.wbgua} / {self.x_studio_wbgua}"})

                                body = f"{sale_line.name} Wb/guía: {sl_wbgua_anterior} ---> {sale_line.wbgua}"
                                order_line_obj.message_post(body=body)
                            else:
                                sale_line.write({'wbgua': self.x_studio_wbgua})
                                body = f"{sale_line.name} Wb/guía: {sale_line.wbgua}"
                                order_line_obj.message_post(body=body)

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(
                self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(
            cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(
            cancel_backorder=False)._action_done()
        return True


class PurchaseOrderInherit(models.Model):

    _inherit = 'purchase.order'

    wbgua = fields.Char(string='WB/Guía', default='')

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrderInherit, self)._prepare_invoice()
        invoice_vals['wbgua_account_move'] = self.wbgua

        return invoice_vals

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append(
                            (0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            # Creamos un set con wbgua
            wbgua_set = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
                # Si viene del mismo proveedor lo agregamos al set y lo actualizamos al ref_invoice_vals
                wbgua_set.add(invoice_vals['wbgua_account_move'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                'wbgua_account_move': ' / '.join(wbgua_set)
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(
            default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # Creamos el mensaje en el chatter para los ordenes o orden de compra asociada al invoice
        for record in self:
            body = "Factura de proveedor creada"
            record.message_post(body=body)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total)
                       < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)


class SaleOrderInherit(models.Model):

    _inherit = 'sale.order'

    wbgua = fields.Char(string="WB/Guia", default='')

    def _create_invoices(self, **option_values):
        res = super()._create_invoices(**option_values)

        for record in self:
            body = "Factura de cliente creada"
            record.message_post(body=body)

        return res


class SaleOrderLineInherit(models.Model):

    _inherit = 'sale.order.line'

    wbgua = fields.Char(string="WB/Guia", default='')

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res["wbgua_related"] = self.wbgua
        return res


class TransportEntryInherit(models.Model):

    _inherit = 'transport.entry'

    sale_order_id = fields.Many2one(
        related='picking_id.sale_id')

    purchase_order_id = fields.Many2one(
        related='picking_id.purchase_order'
    )


class AccountMoveInherit(models.Model):

    _inherit = 'account.move'

    wbgua_account_move = fields.Char(string="WB/Guía", default='')


class AccountMoveLineInherit(models.Model):

    _inherit = 'account.move.line'

    wbgua_related = fields.Char(default='', string="WB/Guía")
