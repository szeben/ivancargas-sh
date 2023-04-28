# -*- coding: utf-8 -*-
{
    'name': "Trazabilidad entre OC, OV, viajes y WB",

    'summary': """
        Enlaza los WB a las Órdenes de venta y compra, según el viaje realizado""",

    'description': """
        Enlaza los WB a las Órdenes de venta y compra, según el viaje realizado.
    """,

    'author': "Techne Studio IT & Consulting",
    'website': "https://technestudioit.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'sale', 'purchase', 'web', 'web_studio', 'transport_module', 'print_consolidated_invoice'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/ivan_cargas_inherit_view_report.xml',
        'report/forma_libre_inherit_view_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
