# -*- coding: utf-8 -*-

import math
from odoo import _, api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    withholding_type = fields.Selection(
        selection=[
            ("iva", "Retención sobre IVA"),
            ("islr", "Retención sobre ISLR"),
        ],
        string="Retención de tipo"
    )
    withholding_amount = fields.Float(
        string="Importe de retención",
        digits=(16, 4),
        default=0.0
    )

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None, use_withholding=False):
        self.ensure_one()
        amount = self.amount

        if use_withholding and (self.withholding_type in {"iva", "islr"}):
            amount = self.withholding_amount or amount

        if self.amount_type == 'fixed':
            if base_amount:
                return math.copysign(quantity, base_amount) * amount
            else:
                return quantity * amount

        price_include = self._context.get(
            'force_price_include', self.price_include)

        if self.amount_type == 'percent' and not price_include:
            return base_amount * amount / 100

        if self.amount_type == 'percent' and price_include:
            return base_amount - (base_amount / (1 + amount / 100))

        if self.amount_type == 'division' and not price_include:
            return base_amount / (1 - amount / 100) - base_amount if (1 - amount / 100) else 0.0

        if self.amount_type == 'division' and price_include:
            return base_amount - (base_amount * (amount / 100))


class AccountMoveWithHoldings(models.Model):
    _inherit = "account.move"

    invoice_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string="Retención al IVA",
        domain=[
            ("withholding_type", "=", "iva"),
            ("type_tax_use", "=", "purchase"),
            ("active", "=", True)
        ],
    )
    withholding_iva = fields.Monetary(
        string='Retención del IVA',
        store=True,
        compute='_compute_withholding',
        currency_field='company_currency_id'
    )
    withholding_islr = fields.Monetary(
        string='Retención del ISLR',
        store=True,
        compute='_compute_withholding',
        currency_field='company_currency_id'
    )

    @api.depends('invoice_tax_id', 'amount_tax')
    def _compute_withholding(self):
        for move in self:
            if move._payment_state_matters():
                amount_total_withholding_islr = 0.0
                amount_total_withholding_iva = 0.0

                for line in move.line_ids:
                    if line.tax_line_id:
                        if line.tax_line_id.withholding_type == "iva":
                            amount_total_withholding_iva += line.amount_currency
                        elif line.tax_line_id.withholding_type == "islr":
                            amount_total_withholding_islr += line.amount_currency

                move.withholding_iva = amount_total_withholding_iva
                move.withholding_islr = amount_total_withholding_islr

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        """ Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * base_line.price_unit * \
                    (1 - (base_line.discount / 100.0))
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (
                    tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency

            return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=move.always_tax_exigible,
            )

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        amount_total_tax = 0.0
        amount_total_withholding_irsl = 0.0
        sign = 1 if self.move_type == 'entry' or self.is_outbound() else -1

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Calculando retensiones ISLR
            amount_tax = sum(
                tax.get("amount") for tax in compute_all_vals.get("taxes", [])
            )
            amount_total_tax += amount_tax

            withholding = line.tax_ids.filtered(
                lambda tax: tax.withholding_type == "islr")
            if withholding:
                withholding.ensure_one()
                amount_withholding_irls = sign * withholding._compute_amount(
                    amount_tax, 0, use_withholding=True
                )
                index = list(tax.get("id") for tax in compute_all_vals.get("taxes", [])).index(
                    withholding._origin.id
                )
                amount_total_withholding_irsl += amount_withholding_irls
                compute_all_vals["total_included"] += amount_withholding_irls
                compute_all_vals["taxes"][index]['amount'] = amount_withholding_irls

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(
                    line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(
                    tax_vals['base'],
                    tax_repartition_line,
                    tax_vals['group']
                )
                taxes_map_entry['grouping_dict'] = grouping_dict

        # Calcula retensiones para el IVA
        if self.invoice_tax_id:
            tax_vals = self.invoice_tax_id._origin.with_context(force_sign=self._get_tax_force_sign()).compute_all(
                price_unit=0,
                currency=self.currency_id,
                partner=self.partner_id
            ).get("taxes")[0]
            tax_vals["amount"] = self.invoice_tax_id._compute_amount(
                (sign*amount_total_tax) - amount_total_withholding_irsl, 0, use_withholding=True
            )
            grouping_dict = self._get_tax_grouping_key_from_base_line(
                line, tax_vals)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)

            tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                tax_vals['tax_repartition_line_id'])
            tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

            taxes_map_entry = taxes_map.setdefault(grouping_key, {
                'tax_line': None,
                'amount': 0.0,
                'tax_base_amount': 0.0,
                'grouping_dict': False,
            })
            taxes_map_entry['amount'] += tax_vals['amount']
            taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(
                tax_vals['base'],
                tax_repartition_line,
                tax_vals['group']
            )
            taxes_map_entry['grouping_dict'] = grouping_dict

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(
                taxes_map_entry['grouping_dict']['currency_id'])

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(
                taxes_map_entry['tax_base_amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self)
            )

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env[
                    'account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(
                    taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))
