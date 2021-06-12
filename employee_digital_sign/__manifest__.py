# -*- coding: utf-8 -*-
{
    'name': "Digital signature",
    'summary': """Adds the ability to configure where the receipt will be signed, 
    and automatically generate a signature from the username. """,
    'author': "Calix",
    'website': "www.calyxservicios.com.ar",
    'category': 'Employee',
    'version': '2.0',

    'depends': ['employee_salary'],

    'data': [
        'security/ir.model.access.csv',
        'views/config_sign_views.xml',
        'views/employee_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
