# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Download Technical sheet",
    "summary": """
        This module is use for download technical sheet for product""",
    "author": "Calyx Servicios S.A.",
    "maintainers": ["GeorginaGuzman"],
    "website": "http://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Custom",
    "version": "14.0.1.0.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": [], "bin": []},
    "depends": ['product'],
    "data": [
        "view/product_feature_view.xml",
        "view/product_attch_website.xml",
        "view/assets.xml",
    ],
}
