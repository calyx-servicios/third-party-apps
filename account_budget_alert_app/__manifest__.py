# -*- coding: utf-8 -*-

{
    'name' : 'Account Budget Limit Alert-Validation Warning',
    'author': "Edge Technologies",
    'version' : '13.0.1.1',
    'live_test_url':'https://youtu.be/Q-46v4WzE0M',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'Accounting Budget Limit Alert Budget limit Warning against Purchase budget limit alerts against Bill budget exceed alerts budget limit alert accounting budget validation against purchase budget integration budget warning limit exceed warning on budget',
    'description' : """
            Allow Accounting Budget Limit Alert/Warning on confirm Purchase Order and validate Vendor Bill
    """,
    "license" : "OPL-1",
    'depends' : ['base','purchase','account','stock'],
    'data': [
            'security/ir.model.access.csv',
            'security/account_budget_security.xml',
            'views/account_budget_views.xml',
            'views/account_analytic_account_views.xml',
            'views/budget_view.xml',
            ],
    'qweb' : [],
    'demo': ['data/account_budget_demo.xml'],
    'installable' : True,
    'auto_install' : False,
    'price': 58,
    'category' : 'Accounting',
    'currency': "EUR",
}
