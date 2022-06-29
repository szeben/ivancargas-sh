# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, models, exceptions
from odoo.fields import Datetime
from odoo.tools.misc import formatLang


VAT_DEFAULT = 'XXXXX'


class MixinTaxWithholdingReport:
    type_withholding = "iva"

    def validate_record(self, record):
        if not record.invoice_date:
            raise exceptions.ValidationError(
                "Se requiere la fecha de Facturación/Reembolso para validar este documento"
            )

        if not record.reference_number:
            raise exceptions.ValidationError(
                "La retención requiere el Número de factura"
            )

        if not record.invoice_control_number:
            raise exceptions.ValidationError(
                "La retención requiere el Número de control de factura"
            )

    def now(self):
        return Datetime.context_timestamp(self, datetime.now())

    def extract_data_by_default(self, record):
        return {
            'company_name': self.env.company.name.upper(),
            'company_vat': (
                self.env.company.company_registry.upper()
                if self.env.company.company_registry
                else VAT_DEFAULT
            ),
            'vendor_name': record.partner_id.name.upper(),
            'vendor_vat': record.partner_id.vat.upper() if record.partner_id.vat else VAT_DEFAULT,
            'amount_base': self.format_lang(record.amount_untaxed),
            'invoice_date': record.invoice_date,
            'invoice_control_number': record.invoice_control_number or "N/A",
            'reference_number': record.reference_number or (
                record.name if record.state == "posted" else "Por definir"
            )
        }

    def get_validated_data(self, record):
        self.validate_record(record)
        data = self.extract_data(record) or {}
        data.update(self.extract_data_by_default(record))
        return type("TaxWithholdingData", (object,), data)

    def extract_data(self, record):
        pass

    def get_data(self, records):
        return list(map(self.get_validated_data, records))

    def format_lang(self, value):
        return formatLang(self.env, value)


class TaxWithholdingIVAReport(MixinTaxWithholdingReport, models.AbstractModel):
    _name = 'report.tax_withholdings.template_tax_withholding_iva'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'tax_withholdings.template_tax_withholding_iva')
        obj = self.env[report.model].browse(docids)
        return {
            'data': self.get_data(obj),
            'now': self.now()
        }

    def extract_data(self, record):
        sign = -1
        withholding_iva = sign*record.withholding_iva
        withholding_islr = sign*(record.withholding_islr or 0.0)
        data = {
            "aliquot": sign*record.invoice_tax_id.amount,
            "amount_tax": record.amount_tax + withholding_iva,
            "amount_total": record.amount_total + withholding_islr,
            "amount_withholding": withholding_iva,
            "total_purchase": record.amount_total + withholding_iva + withholding_islr
        }
        data = {key: self.format_lang(value) for key, value in data.items()}
        if record.sequence_withholding_iva:
            data["number_withholding"] = f"{record.invoice_date:%Y%m}{record.sequence_withholding_iva:>08}"
        else:
            data["number_withholding"] = 'Por definir'
        data["company_street"] = ' '.join([
            self.env.company.street or '',
            self.env.company.street2 or ''
        ]).upper()
        return data

    def validate_record(self, record):
        super().validate_record(record)

        if (record.withholding_iva or 0.0) >= 0.0:
            raise exceptions.UserError(
                "Esta factura no tiene retención"
            )


class TaxWithholdingISLRReport(MixinTaxWithholdingReport, models.AbstractModel):
    _name = 'report.tax_withholdings.template_tax_withholding_islr'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'tax_withholdings.template_tax_withholding_islr')
        obj = self.env[report.model].browse(docids)
        return {
            'data': self.get_data(obj),
            'now': self.now()
        }

    def extract_data(self, record):
        sign = -1
        withholding_islr = sign*record.withholding_islr
        withholding_iva = sign*(record.withholding_iva or 0.0)
        data = {
            "amount_total": record.amount_total + withholding_iva,
            "amount_withholding": withholding_islr,
            "total_purchase": record.amount_total + withholding_iva + withholding_islr
        }

        first_line = next(
            filter(
                lambda l: l.tax_line_id
                and l.tax_line_id.withholding_type == "islr"
                and l.tax_line_id.amount != 0.0,
                record.line_ids,
            )
        )
        data["percentage"] = sign*first_line.tax_line_id.amount

        data = {key: self.format_lang(value) for key, value in data.items()}
        return data

    def validate_record(self, record):
        super().validate_record(record)

        if (record.withholding_islr or 0.0) >= 0.0:
            raise exceptions.UserError(
                "Esta factura no tiene retención"
            )
