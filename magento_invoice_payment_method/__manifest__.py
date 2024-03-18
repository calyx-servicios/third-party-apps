{
    "name": "Magento Invoice Payment Method",
    "summary": """
        This module adds referential field for Magento Payment Method into invoice. 
    """,
    "author": "Calyx Servicios S.A.",
    "maintainers": ["gpperez","EnzoGonzalezDev"],
    "website": "https://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Connector",
    "version": "13.0.2.0.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "depends": ['globalteckz_magento_2',],
    'data': ['views/account_invoice_view.xml'],
    'installable': True,
    'application': False,
}
