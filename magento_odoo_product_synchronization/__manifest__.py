{
    "name": "Magento Odoo Product Synchronization",
    "summary": """
        This module extends magento 2 module synchronize magento id products on odoo by SKU number 
    """,
    "author": "Calyx Servicios S.A.",
    "maintainers": ["gpperez"],
    "website": "https://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Connector",
    "version": "13.0.1.0.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "depends": ['globalteckz_magento_2',],
    'data': ['views/gt_magento_view.xml'],
    'installable': True,
    'application': False,
}
