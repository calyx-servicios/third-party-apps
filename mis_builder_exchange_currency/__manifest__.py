{
    "name": "Mis Builder - Exchange Currency",
    "summary": """
        Summary of the module's purpose
    """,
    "author": "Calyx Servicios S.A.",
    "maintainers": ["gpperez"],
    "website": "https://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Reporting",
    "version": "13.0.1.0.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "depends": ["mis_builder",
                "account_ux"],
    ## XML Data files
    'data': [
        #'security/ir.model.access.csv',
        'views/account_move.xml',
    ],

}
