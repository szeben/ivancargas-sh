# -*- coding: utf-8 -*-
{
    'name': "Facturas consolidadas y en forma libre",

    'summary': """
        Incluye una forma libre de factura y dos formatos de
        factura consolidada (facturas de clientes)
    """,

    'description': """
        Incluye una forma libre de factura (sin encabezado ni pie de página)
        y dos formatos (con encabezado y en forma libre) de facturas
        consolidadas, agrupando líneas de facturación por producto,
        etiqueta y ruta.
    """,

    'author': "Techne Studio IT & Consulting",
    'website': "https://technestudioit.com/",

    'license': "Other proprietary",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'report/print_consolidated_invoice_reports.xml',
        'report/print_consolidated_invoice_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
