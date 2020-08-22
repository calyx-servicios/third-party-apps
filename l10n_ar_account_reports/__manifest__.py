##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Accounting Reports Customized for Argentina',
    'version': '11.0.1.10.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': '',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'account_reports',
        'account_debt_management',
        'l10n_ar_account',
        'account_check',
    ],
    'data': [
        'security/security.xml',
        'views/account_journal_dashboard_view.xml',
        'views/account_debt_report_line_views.xml',
        'views/res_partner_views.xml',
        'reports/invoice_analysis.xml',
        'wizards/checks_to_date_view.xml',
        'reports/account_checks_to_date_report.xml',
        # desactivamos para no confundir porque todavia no esta
        # 'data/account_financial_report_data.xml',
        # analizar
        # 'wizards/res_config_settings_views.xml',
        # 'views/report_financial.xml',
        # 'views/report_followup.xml',
        'views/tax_report_view.xml',
        # 'data/vat_position_report.xml',
        # 'data/iibb_position_report.xml',
        # 'data/profits_position_report.xml',
    ],
    'demo': [
        'demo/res_config_demo.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
