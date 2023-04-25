# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMoveReportCustom(models.Model):
    _inherit = "account.move"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if self._context.get('default_move_type') != 'out_invoice':
            remove_report_ids = [
                self.env.ref(f"print_consolidated_invoice.{name}").id for name in (
                    "report_invoice_freeform_print_consolidated_invoice",
                    "report_invoice_print_consolidated_invoice",
                    "report_invoice_print_consolidated_invoice_freeform",
                )
            ]
            if view_type == 'tree' and remove_report_ids and \
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

    @api.model
    @api.depends('line_ids')
    def get_grouped_lines_by_product(self):
        lines = self.invoice_line_ids.sorted(key=lambda l: (-l.sequence, l.date, l.move_name, -l.id), reverse=True)
        groups = {}
        for line in lines:
            print(line.currency_id)
            key = str(line.product_id) + str(line.name) + str(line.order_route) + str(line.x_studio_precio_unitario_bs)

            if key in groups:
                groups[key]['quantity'] += line.quantity
                groups[key]['credit'] += line.credit
            else:
                groups[key] = {
                    'name': line.name,
                    'order_route': line.order_route,
                    'price_unit': line.x_studio_precio_unitario_bs,
                    'currency_id': line.currency_id,
                    'tax_ids': line.tax_ids,
                    'quantity': line.quantity,
                    'uom': f" {line.product_uom_id.name}",
                    'credit': line.credit
                }

        for group in groups.values():
            quantity = "{:,.4f}".format(group['quantity']).replace(",", "#").replace(".", ",").replace("#", ".")
            price_unit = "{:,.3f}".format(group['price_unit']).replace(",", "#").replace(".", ",").replace("#", ".")
            credit = "{:,.2f}".format(group['credit']).replace(",", "#").replace(".", ",").replace("#", ".")
            group['quantity'] = quantity
            group['price_unit'] = price_unit
            group['credit'] = f"{credit} Bs"

        return groups.values()