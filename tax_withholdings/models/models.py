# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, exceptions

VAT_DEFAULT = 'XXXXX'


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
        ],
        required=False,
    )
    withholding_iva = fields.Monetary(
        string='Retención del IVA ',
        store=True,
        compute='_compute_withholding',
        currency_field='company_currency_id'
    )
    withholding_islr = fields.Monetary(
        string='Retención del ISLR ',
        store=True,
        compute='_compute_withholding',
        currency_field='company_currency_id'
    )
    sequence_withholding_iva = fields.Char(
        string="Secuencia de la retención del IVA",
        compute="_compute_secuence_withholding",
        store=True,
        copy=False
    )
    sequence_withholding_islr = fields.Char(
        string="Secuencia de la retención del ISLR",
        compute="_compute_secuence_withholding",
        store=True,
        copy=False
    )
    reference_number = fields.Char(
        string="Número de factura",
        copy=False
    )
    invoice_control_number = fields.Char(
        string="Número de control de factura",
        copy=False
    )
    subtracting = fields.Monetary(
        string='Sustraendo',
        default=0.0,
        currency_field='company_currency_id'
    )

    # Fields to export
    withholding_agent_vat = fields.Char(
        string="RIF del Agente de Retención",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True
    )
    retained_subject_vat = fields.Char(
        string="RIF del Sujeto Retenido",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True
    )
    withholding_number = fields.Char(
        string="Número de retención",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True
    )
    aliquot_iva = fields.Float(
        string="Alícuota del IVA",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True
    )
    withholding_percentage_islr = fields.Float(
        string="Porcentaje de retención",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True
    )
    amount_tax_iva = fields.Monetary(
        string="Total de impuestos (IVA)",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    amount_tax_islr = fields.Monetary(
        string="Total de impuestos (ISLR)",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    amount_total_iva = fields.Monetary(
        string="Total menos retenciones IVA",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    vat_exempt_amount_iva = fields.Monetary(
        string="Monto excento de IVA",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    vat_exempt_amount_islr = fields.Monetary(
        string="Monto excento de ISLR",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    amount_total_islr = fields.Monetary(
        string="Total menos retenciones ISLR",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    amount_total_purchase = fields.Monetary(
        string="Total de la compra",
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    withholding_opp_iva = fields.Monetary(
        string='Retención del IVA',
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    withholding_opp_islr = fields.Monetary(
        string='Retención del ISLR',
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )
    total_withheld = fields.Monetary(
        string='Total retenido',
        compute="_compute_fields_to_export",
        store=False,
        copy=False,
        readonly=True,
        currency_field='company_currency_id'
    )

    @api.depends('invoice_tax_id', 'amount_tax', 'line_ids.tax_line_id')
    def _compute_withholding(self):
        for move in self:
            amount_total_withholding_iva = 0.0
            amount_total_withholding_islr = 0.0

            if move._payment_state_matters():
                for line in move.line_ids:
                    if line.tax_line_id:
                        if line.tax_line_id.withholding_type == "iva":
                            amount_total_withholding_iva += line.amount_currency
                        elif line.tax_line_id.withholding_type == "islr":
                            amount_total_withholding_islr += line.amount_currency

            move.withholding_iva = amount_total_withholding_iva
            move.withholding_islr = amount_total_withholding_islr

    @api.depends("state", "withholding_iva", "withholding_islr")
    def _compute_secuence_withholding(self):
        for move in self:
            if move.state == "posted":
                if ((move.withholding_iva or 0.0) < 0.0) and not move.sequence_withholding_iva:
                    move.sequence_withholding_iva = self.env["ir.sequence"].next_by_code(
                        "account.move.withholding.iva")
                if ((move.withholding_islr or 0.0) < 0.0) and not move.sequence_withholding_islr:
                    move.sequence_withholding_islr = self.env["ir.sequence"].next_by_code(
                        "account.move.withholding.islr")

    @api.depends("invoice_tax_id",
                 "subtracting",
                 "sequence_withholding_iva",
                 "sequence_withholding_islr",
                 "withholding_iva",
                 "withholding_islr")
    def _compute_fields_to_export(self):
        for move in self:
            move.withholding_agent_vat = (
                self.env.company.company_registry.upper()
                if self.env.company.company_registry
                else VAT_DEFAULT
            )

            sign = -1
            move.withholding_opp_iva = withholding_iva = sign * \
                (move.withholding_iva or 0.0)
            move.withholding_opp_islr = withholding_islr = sign * \
                (move.withholding_islr or 0.0) + move.subtracting

            if move.move_type in {'in_invoice', 'in_refund', 'in_receipt'} and (
                withholding_iva != 0.0 or withholding_islr != 0.0
            ):
                move.retained_subject_vat = (
                    move.partner_id.vat.upper()
                    if move.partner_id.vat
                    else VAT_DEFAULT
                )

                move.amount_total_purchase = move.amount_total + \
                    withholding_iva + withholding_islr

                if withholding_iva != 0.0:
                    move.withholding_number = f"{move.invoice_date:%Y%m}{move.sequence_withholding_iva:>08}"
                    move.amount_tax_iva = move.amount_tax + withholding_iva
                    move.amount_total_iva = move.amount_total + withholding_islr

                    aliquot_iva = 0.0
                    vat_exempt_amount = 0.0

                    for line in move.line_ids:
                        if (
                            not line.tax_repartition_line_id
                            and not line.exclude_from_invoice_tab
                            and (
                                not line.tax_ids or not any(
                                    tax.amount != 0.0 for tax in line.tax_ids
                                    if not tax.withholding_type
                                )
                            )
                        ):
                            vat_exempt_amount += line.amount_currency
                        elif (
                            aliquot_iva == 0.0
                            and line.tax_line_id
                            and line.tax_line_id.withholding_type == False
                            and line.tax_line_id.amount != 0.0
                        ):
                            aliquot_iva = line.tax_line_id.amount

                    move.aliquot_iva = aliquot_iva
                    move.vat_exempt_amount_iva = vat_exempt_amount

                else:
                    move.withholding_number = "0"
                    move.aliquot_iva = 0
                    move.amount_tax_iva = 0
                    move.amount_total_iva = 0
                    move.vat_exempt_amount_iva = 0

                if withholding_islr != 0.0:
                    move.amount_tax_islr = move.amount_tax + withholding_islr
                    move.amount_total_islr = move.amount_total + withholding_iva
                    move.total_withheld = withholding_islr - move.subtracting

                    withholding_percentage_islr = 0.0
                    vat_exempt_amount = 0.0

                    for line in move.line_ids:
                        if (
                            not line.tax_repartition_line_id
                            and not line.exclude_from_invoice_tab
                            and (
                                not line.tax_ids or not any(
                                    tax.amount != 0.0 for tax in line.tax_ids
                                    if tax.withholding_type == "islr"
                                )
                            )
                        ):
                            vat_exempt_amount += line.amount_currency
                        elif (
                            withholding_percentage_islr == 0.0
                            and line.tax_line_id
                            and line.tax_line_id.withholding_type == "islr"
                            and line.tax_line_id.amount != 0.0
                        ):
                            withholding_percentage_islr = line.tax_line_id.amount

                    move.vat_exempt_amount_islr = vat_exempt_amount
                    move.withholding_percentage_islr = sign*withholding_percentage_islr

                else:
                    move.amount_tax_islr = 0
                    move.amount_total_islr = 0
                    move.withholding_percentage_islr = 0
                    move.vat_exempt_amount_islr = 0
                    move.total_withheld = 0

            else:
                move.retained_subject_vat = "0"
                move.amount_total_purchase = 0
                move.withholding_number = "0"
                move.aliquot_iva = 0
                move.amount_tax_iva = 0
                move.amount_total_iva = 0
                move.amount_tax_islr = 0
                move.amount_total_islr = 0
                move.withholding_percentage_islr = 0
                move.vat_exempt_amount = 0
                move.total_withheld = 0

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        '''
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
                price_unit_wo_discount = sign * base_line.price_unit * (
                    1 - (base_line.discount / 100.0)
                )
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
        sign = 1 if self.move_type == 'entry' or self.is_outbound() else -1

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Calculando total de impuestos
            if self.move_type in {'in_invoice', 'in_refund', 'in_receipt'}:
                amount_total_tax += sum(
                    tax.get("amount") for tax in compute_all_vals.get("taxes", [])
                    if tax.get("amount") and (tax.get("amount")/abs(tax.get("amount")) == sign)
                )

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

        # === Calcula retensiones para el IVA ===
        if self.invoice_tax_id and (self.move_type in {'in_invoice', 'in_refund', 'in_receipt'}):
            tax_vals = self.invoice_tax_id._origin.with_context(force_sign=self._get_tax_force_sign()).compute_all(
                price_unit=0,
                currency=self.currency_id,
                partner=self.partner_id
            ).get("taxes")[0]
            tax_vals["amount"] = self.invoice_tax_id._compute_amount(
                sign*amount_total_tax, 0)
            grouping_dict = self._get_tax_grouping_key_from_base_line(
                line, tax_vals)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)

            tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                tax_vals['tax_repartition_line_id'])

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

            if taxes_map_entry["tax_line"] and taxes_map_entry["tax_line"].tax_line_id.withholding_type == "islr":
                taxes_map_entry['amount'] += self.subtracting

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
                create_method = (
                    in_draft_mode and self.env['account.move.line'].new
                    or self.env['account.move.line'].create
                )
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if self._context.get("default_move_type") not in ('in_invoice', 'in_refund', 'in_receipt'):
            remove_report_ids = [
                self.env.ref(f"tax_withholdings.{name}").id for name in (
                    "report_tax_withholding_iva",
                    "report_tax_withholding_islr",
                )
            ]
            if view_type == 'form' and remove_report_ids and \
                    toolbar and res['toolbar'] and res['toolbar'].get('print'):
                remove_report_records = list(filter(
                    lambda rec: rec.get("id") in remove_report_ids,
                    res['toolbar'].get('print')
                ))
                if remove_report_records:
                    for report_record in remove_report_records:
                        if report_record:
                            res['toolbar'].get('print').remove(report_record)
        return res

    error_message_subtracting = _(
        'El valor del Sustraendo de ISLR debe ser menor o igual '
        'a la retención de ISLR. Por favor, cambie el valor del '
        'sustraendo a "0,00" si no aplica o a un valor menor o '
        'igual a la retención'
    )

    @api.onchange("invoice_tax_id")
    def _onchange_invoice_tax(self):
        if self.line_ids:
            self._recompute_dynamic_lines(recompute_all_taxes=True)

    @api.onchange("subtracting")
    def _onchance_subtracting(self):
        self.ensure_one()
        sign = -1 if self.move_type == 'entry' or self.is_outbound() else 1

        if self.subtracting > sign*self.withholding_islr:
            self.subtracting = 0.0
            raise exceptions.ValidationError(
                self.error_message_subtracting
            )

        if self.line_ids:
            self._recompute_dynamic_lines(recompute_all_taxes=True)

    @api.constrains('subtracting')
    def _check_subtracting(self):
        for move in self:
            sign = -1 if move.move_type == 'entry' or move.is_outbound() else 1
            if move.subtracting > sign*move.withholding_islr:
                raise exceptions.ValidationError(
                    self.error_message_subtracting
                )
