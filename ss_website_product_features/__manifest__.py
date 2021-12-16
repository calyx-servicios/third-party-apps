# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Website Product Technical Fatures',
    'version' : '13.0',
    "author": "Simple Apps",
    "application": True,
    'summary': 'Product technical features on website, website product features, website product specifications',
    'sequence': 15,
    'description': """
    Product technical features on website, website product features, website product specifications
    """,
    'category': 'General',
    'depends' : ['website_sale'],
    'data': [
		'security/ir.model.access.csv',
        'security/group_security.xml',
		'views/views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    "images": [
        "static/description/screen.png",
    ],
    "price": "9",
    "currency": "USD",
}
