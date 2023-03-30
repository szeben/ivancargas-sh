# -*- coding: utf-8 -*-
{
    'name': "Adecuaciones en Ordenes de venta",

    'summary': """
        Incorpora campos informativos a las órdenes de venta""",

    'description': """
        Incluye las columnas de Cantidad pedida, Entregada, Facturada y 
        Número de guía en el listado de órdenes de venta, 
        así como el campo “Cantidad por facturar”, 
        correspondiente a la cantidad pendiente por facturar.
    """,

    'author': "Techne Studio IT & Consulting",
    'website': "https://technestudioit.com/",

    'license': "Other proprietary",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'transport_module'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],   
}
