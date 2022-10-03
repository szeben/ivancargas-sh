# -*- coding: utf-8 -*-
{
    'name': "Retenciones ISLR e IVA",

    'summary': """
        Genera las retenciones para impuestos de tipo ISLR e IVA en 
        las ordenes de compra""",

    'description': """
        Permite configurar, generar, imprimir reporte de retencion y 
        exportar la base para entregar al SENIAT de lo correspondiente 
        a las retenciones sobre ISLR e IVA
    """,

    'author': "Techne Studio IT & Consulting",
    'website': "https://technestudioit.com/",

    'license': "Other proprietary",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/tax_withholding_reports.xml',
        'report/tax_withholding_templates.xml',
        'data/template_export_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
