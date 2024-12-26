# -*- coding: utf-8 -*-
{
    'name': 'Transport Management',
    'version': '17.0.1.0.3',
    'summary': """Module for managing transportation services""",
    'description': 'Module that allows you to manage documents, purchases and sales of services performed.',
    "category": "Services",
    'author': 'Bisiach Lucio',
    'company': 'Bisiach Lucio',
    'website': "",
    'depends': ['purchase', 'sale_management','account', 'fleet'],
    'data': [
        'data/ir_sequence.xml',
        'data/default_data.xml',
        'security/ir.model.access.csv',
        'views/menu_item.xml',
        'views/product.xml',
        'views/fleet_vehicle.xml',
        'views/res_partner.xml',
        'views/service.xml',
        'views/tms_settings.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/account_move.xml'
    ],
    'images': [
        'static/description/banner.png'
        ],
    'license': 'AGPL-3',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
