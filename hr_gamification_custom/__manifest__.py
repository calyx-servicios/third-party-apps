# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'HR Gamification custom',
    'version': '1.0',
    'category': 'Human Resources',
    'depends': ['hr_gamification','gamification'],
    'description': """  """,
    'data': [

        'security/gamification_security.xml',
        'security/ir.model.access.csv',
        'wizards/minimun_objective_control_view.xml',
        'views/assets.xml',
        'views/gamification_views.xml',
        'views/gamification_tag_view.xml',
    ],
    'auto_install': True,

}
