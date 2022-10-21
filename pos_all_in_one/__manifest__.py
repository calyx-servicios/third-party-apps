# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "POS All in one -Advance Point of Sale All in one Features",
    "version" : "13.0.2.9",
    "category" : "Point of Sale",
    'summary': 'All in one pos Reprint pos Return POS Stock pos gift import sale from pos pos multi currency payment pos pay later pos internal transfer pos disable payment pos product template pos product operation pos loyalty rewards all pos reports pos stock all pos',
    "description": """
    
        POS all in one -  advance app features pos Reorder pos Reprint pos Coupon Discount pos Order Return POS Stock pos gift pos order all pos all features pos discount pos order list print pos receipt pos item count pos bag charges import sale from pos create quote from pos pos multi currency payment  pos pay later pos internal transfer pos discable payment pos product template pos product create/update pos loyalty rewards pos reports
    
    """,
    "author": "BrowseInfo",
    "website" : "https://www.browseinfo.in",
    "price": 65,
    "currency": 'EUR',
    "depends" : ['base',
                'point_of_sale',
                'pos_hr',
                'pos_orders_all' 
                ],
    "data": [
        'security/ir.model.access.csv',
        'views/assets.xml',  
        'views/pos_orders_list.xml',
        'views/bi_pos_pay_later.xml',      
        'views/pos_internal_transfer.xml',
        'views/pos_multi_currency.xml',
        'views/bi_pos_payment.xml',
        'views/pos_disable_payment.xml',
        'views/pos_product_operation.xml',
        'views/pos_loyalty.xml',
        'views/pos_report.xml',
        'wizard/sales_summary_report.xml',
        'wizard/pos_sale_summary.xml',
        'wizard/pos_payment_xls.xml',
        'wizard/x_report_view.xml',
        'wizard/z_report_view.xml',
        'wizard/top_selling.xml',
        'wizard/top_selling_report.xml',
        'wizard/profit_loss_report.xml',
        'wizard/pos_payment_report.xml',
        'wizard/profit_loss.xml',
        'wizard/pos_payment.xml', 
    ],
    'qweb': [
        'static/src/xml/pos_view_extends.xml',
        'static/src/xml/bi_pos_payment.xml',
        'static/src/xml/pos_internal_transfer.xml',
        'static/src/xml/pos_multi_currency.xml',
        'static/src/xml/pos_disable_payment.xml',
        'static/src/xml/pos_product_operation.xml',
        'static/src/xml/bi_pos_product_template.xml',
        'static/src/xml/bi_pos_reprint_reorder.xml',
        'static/src/xml/pos_report.xml',
        'static/src/xml/pos_loyalty.xml',
        'static/src/xml/bi_pos_pay_later.xml',
        'static/src/xml/pos_orders_list.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://youtu.be/3UcvG6ukjZE',
    "images":["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
