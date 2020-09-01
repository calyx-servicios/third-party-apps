##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class WizardMultiChartsAccounts(models.TransientModel):
    """
    Lo hacemos en este modelo y este método porque en de _prepare_all_journals
    'account.chart.template' se llama solo para el journal sin padre
    y el account ref solo tiene las de ese chart, entonces no tenemos
    data de cuentas que instalan chart hijos (por ej, iva)
    """
    _inherit = 'wizard.multi.charts.accounts'

    @api.multi
    def _create_bank_journals_from_o2m(self, company, acc_template_ref):
        res = super(
            WizardMultiChartsAccounts, self)._create_bank_journals_from_o2m(
            company, acc_template_ref)

        if company.localization != 'argentina':
            return res

        ref = self.env.ref

        def get_account(ext_id):
            """
            Helper para obtener referencia a alguna cuenta
            """
            return acc_template_ref.get(ref('l10n_ar_chart.%s' % ext_id).id)

        # add more journals commonly used in argentina localization
        journals = [
            ('Liquidación de IIBB', 'IIBB', 'allow_per_line', 'iibb_sufrido',
                ref('l10n_ar_account.par_iibb_pagar'),
                get_account('base_iibb_a_pagar'),
                get_account('base_iibb_a_pagar'),
                ref('l10n_ar_account.tax_tag_a_cuenta_iibb'))
        ]

        chart = company.chart_template_id
        ri_chart = ref('l10n_ar_chart.l10nar_ri_chart_template', False)
        ex_chart = ref('l10n_ar_chart.l10nar_ex_chart_template', False)

        # iva solo para RI
        if chart == ri_chart:
            journals += [
                ('Liquidación de IVA', 'IVA', 'yes', False,
                    # ref('l10n_ar_account_reports.'
                    #     'account_financial_report_vat_position'),
                    ref('l10n_ar_account.partner_afip'),
                    get_account('ri_iva_saldo_tecnico_favor'),
                    get_account('ri_iva_saldo_a_pagar'),
                    ref('l10n_ar_account.tax_tag_a_cuenta_iva'))]

        account_withholding_automatic = self.env['ir.module.module'].search([
            ('name', '=', 'account_withholding_automatic'),
            ('state', '=', 'installed')])
        # por ahora, por mas que no tenga retenciones automaticas,
        # creamos los daiarios de liquidacion ya que es mas facil desactivarlos
        # que crearlos luego, y si es un ri lo mas probable es que deba
        # tenerlos

        # estas para mono no van, para exento y ri si
        if chart in (ri_chart, ex_chart):
            journals += [
                ('Liquidación de Ganancias', 'GAN', 'yes', False,
                    # ref('l10n_ar_account_reports.'
                    #     'account_financial_report_profits_position'),
                    ref('l10n_ar_account.partner_afip'),
                    get_account('base_saldo_favor_ganancias'),
                    get_account('base_impuesto_ganancias_a_pagar'),
                    ref('l10n_ar_account.tax_tag_a_cuenta_ganancias')),
                # only if account_withholding_automatic installed we
                # set sicore_aplicado for txt
                ('Liquidación SICORE Aplicado', 'SICORE', 'allow_per_line',
                    account_withholding_automatic and 'sicore_aplicado',
                    ref('l10n_ar_account.partner_afip'),
                    get_account('ri_retencion_sicore_a_pagar'),
                    get_account('ri_retencion_sicore_a_pagar'),
                    ref('l10n_ar_account.tag_ret_perc_sicore_aplicada')),
                # TODO borrar, sicore aplicado se liquidaría todo junto
                # ('Liquidación SICORE (Ganancias)', 'GA_AP', 'allow_per_line',
                #     ref('l10n_ar_account.partner_afip'),
                #     get_account('ri_retencion_ganancias_a_pagar'),
                #     get_account('ri_retencion_ganancias_a_pagar'),
                #     ref('l10n_ar_account.tag_ret_perc_ganancias_aplicada')),
                ('Liquidación IIBB Aplicado', 'IB_AP', 'allow_per_line',
                    False,  # 'iibb_aplicado', (Se debe elegir segun provincia)
                    ref('l10n_ar_account.par_iibb_pagar'),
                    # TODO flatan crear estas cuentas!
                    get_account('ri_retencion_iibb_a_pagar'),
                    get_account('ri_retencion_iibb_a_pagar'),
                    ref('l10n_ar_account.tag_ret_perc_iibb_aplicada')),
            ]

        # for name, code, tax, report, partner, credit_id, debit_id, tag \
        for name, code, type, tax, partner, credit_id, debit_id, tag \
                in journals:
            # journal_data.append({
            self.env['account.journal'].create({
                'type': 'general',
                'name': name,
                'code': code,
                'tax_settlement': type,
                'settlement_tax': tax,
                # 'settlement_financial_report_id': report and report.id,
                'settlement_partner_id': partner and partner.id,
                'default_credit_account_id': credit_id,
                'default_debit_account_id': debit_id,
                'company_id': company.id,
                # al final hicimos otro dashboard
                'show_on_dashboard': False,
                'update_posted': True,
                'settlement_account_tag_ids': tag and [(4, tag.id, False)],
            })

        return res
