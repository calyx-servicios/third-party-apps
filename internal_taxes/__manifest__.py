# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Internal Taxes",
    "summary": """
        Custom page in the products for internal taxes""",
    "author": "Calyx Servicios S.A.",
    "maintainers": ["gabbiiperez"],
    "website": "http://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Technical Settings",
    "version": "13.0.1.0.0",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
    ],
    "data": [
        "views/account_tax_views.xml",
    ],
}

