# -*- coding: utf-8 -*-

import json
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.tools.misc import formatLang


class AccountTax(models.Model):
    _inherit = "account.tax"

    withholding_type = fields.Selection(
        selection=[
            ("iva", "Retención sobre IVA"),
            ("islr", "Retención sobre ISLR"),
        ],
        string="Retención de tipo"
    )


class AccountMoveWithHoldings(models.Model):
    _inherit = "account.move"

    invoice_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string="Retención al IVA",
        domain=[
            ("withholding_type", "=", "iva"),
            ("type_tax_use", "=", "purchase"),
            ("active", "=", True)
        ]
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
            # withholding IVA
            if move.invoice_tax_id:
                if move.invoice_tax_id.amount_type == "percent":
                    move.withholding_iva = move.amount_tax*move.invoice_tax_id.amount/100.0
                elif move.invoice_tax_id.amount_type == "fixed":
                    move.withholding_iva = move.amount_tax - move.invoice_tax_id.amount
                else:
                    move.withholding_iva = False

            move.withholding_islr = False

    def _prepare_tax_lines_data_for_totals_from_invoice(self, tax_line_id_filter=None, tax_ids_filter=None):
        self.ensure_one()

        tax_line_id_filter = tax_line_id_filter or (lambda aml, tax: True)
        tax_ids_filter = tax_ids_filter or (lambda aml, tax: True)

        balance_multiplicator = -1 if self.is_inbound() else 1
        tax_lines_data = []

        for line in self.line_ids:
            if line.tax_line_id and tax_line_id_filter(line, line.tax_line_id):
                tax_lines_data.append({
                    'line_key': 'tax_line_%s' % line.id,
                    'tax_amount': line.amount_currency*balance_multiplicator,
                    'tax': line.tax_line_id,
                })

            if line.tax_ids:
                for base_tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax_ids_filter(line, base_tax):
                        tax_lines_data.append({
                            'line_key': 'base_line_%s' % line.id,
                            'base_amount': line.amount_currency*balance_multiplicator,
                            'tax': base_tax,
                            'tax_affecting_base': line.tax_line_id,
                        })

        return tax_lines_data

    @api.model
    def _get_tax_totals(self, partner, tax_lines_data, amount_total, amount_untaxed, currency):
        lang_env = self.with_context(lang=partner.lang).env
        account_tax = self.env['account.tax']

        grouped_taxes = defaultdict(
            lambda: defaultdict(
                lambda: {
                    'base_amount': 0.0,
                    'tax_amount': 0.0,
                    'base_line_keys': set()
                }
            )
        )
        subtotal_priorities = {}

        for line_data in tax_lines_data:
            tax_group = line_data['tax'].tax_group_id

            # Update subtotals priorities
            if tax_group.preceding_subtotal:
                subtotal_title = tax_group.preceding_subtotal
                new_priority = tax_group.sequence
            else:
                # When needed, the default subtotal is always the most prioritary
                subtotal_title = _("Untaxed Amount")
                new_priority = 0

            if subtotal_title not in subtotal_priorities or new_priority < subtotal_priorities[subtotal_title]:
                subtotal_priorities[subtotal_title] = new_priority

            # Update tax data
            tax_group_vals = grouped_taxes[subtotal_title][tax_group]

            if 'base_amount' in line_data:
                # Base line
                if tax_group == line_data.get('tax_affecting_base', account_tax).tax_group_id:
                    # In case the base has a tax_line_id belonging to the same group as the base tax,
                    # the base for the group will be computed by the base tax's original line (the one with tax_ids and no tax_line_id)
                    continue

                if line_data['line_key'] not in tax_group_vals['base_line_keys']:
                    # If the base line hasn't been taken into account yet, at its amount to the base total.
                    tax_group_vals['base_line_keys'].add(line_data['line_key'])
                    tax_group_vals['base_amount'] += line_data['base_amount']

            else:
                # Tax line
                tax_group_vals['tax_amount'] += line_data['tax_amount']

        # Compute groups_by_subtotal
        groups_by_subtotal = {}
        for subtotal_title, groups in grouped_taxes.items():
            groups_vals = [{
                'tax_group_name': group.name,
                'tax_group_amount': amounts['tax_amount'],
                'tax_group_base_amount': amounts['base_amount'],
                'formatted_tax_group_amount': formatLang(lang_env, amounts['tax_amount'], currency_obj=currency),
                'formatted_tax_group_base_amount': formatLang(lang_env, amounts['base_amount'], currency_obj=currency),
                'tax_group_id': group.id,
                'group_key': '%s-%s' % (subtotal_title, group.id),
            } for group, amounts in sorted(groups.items(), key=lambda l: l[0].sequence)]

            groups_by_subtotal[subtotal_title] = groups_vals

        # Compute subtotals
        subtotals_list = []  # List, so that we preserve their order
        previous_subtotals_tax_amount = 0
        for subtotal_title in sorted((sub for sub in subtotal_priorities), key=lambda x: subtotal_priorities[x]):
            subtotal_value = amount_untaxed + previous_subtotals_tax_amount
            subtotals_list.append({
                'name': subtotal_title,
                'amount': subtotal_value,
                'formatted_amount': formatLang(lang_env, subtotal_value, currency_obj=currency),
            })

            subtotal_tax_amount = sum(
                group_val['tax_group_amount'] for group_val in groups_by_subtotal[subtotal_title]
            )
            previous_subtotals_tax_amount += subtotal_tax_amount

        if self.amount_tax and self.invoice_tax_id:
            amount = self.invoice_tax_id.amount

            if self.invoice_tax_id.amount_type == "percent":
                amount /= 100.0

        # Assign json-formatted result to the field
        return {
            'amount_total': amount_total,
            'amount_untaxed': amount_untaxed,
            'formatted_amount_total': formatLang(lang_env, amount_total, currency_obj=currency),
            'formatted_amount_untaxed': formatLang(lang_env, amount_untaxed, currency_obj=currency),
            'groups_by_subtotal': groups_by_subtotal,
            'subtotals': subtotals_list,
            'allow_tax_edition': False,
        }
