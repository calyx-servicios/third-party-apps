# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.misc import formatLang


class AccountRetAndPercReport(models.AbstractModel):
    _name = "account.ret_and_perc.report"
    _description = "Retentions and Withholdings Report"

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        return formatLang(self.env, value, currency_obj=currency_id)

    @api.model
    def get_lines(self, context_id, line_id=None):
        return self.with_context(
            date_from=context_id.date_from,
            date_to=context_id.date_to,
            state=context_id.all_entries and 'all' or 'posted',
            comparison=False,
            # comparison=context_id.comparison,
            date_from_cmp=context_id.date_from_cmp,
            date_to_cmp=context_id.date_to_cmp,
            # cash_basis=context_id.cash_basis,
            periods_number=context_id.periods_number,
            periods=context_id.get_cmp_periods(),
            context_id=context_id,
            company_ids=context_id.company_ids.ids,
            strict_range=True,
        )._lines()

    @api.model
    def _lines(self):
        context = self.env.context
        date_from = context.get('date_from')
        date_to = context.get('date_to')
        lines = []

        ref = self.env.ref
        # If True, then we add a columns for base, if false, only tax amount
        tax_group_list = [
            (True, ref('l10n_ar_account.tax_group_iva_21')),
            (True, ref('l10n_ar_account.tax_group_iva_10')),
            (False, ref('l10n_ar_account.tax_group_percepcion_iva')),
        ]
        # tax_groups = [x[1] for x in tax_group_list]

        line_id = 0

        for iva in ['Sufrida', 'Aplicada']:
            # TODO ver como scamos esta suma
            line_vals = self._get_lines_vals(
                date_from, date_to, categs_list, tax_group_list)
            print 'line_vals', line_vals
            columns = []
            for base_column, tax_group in tax_group_list:
                if base_column:
                    columns.append(line_vals[tax_group]['base'])
                columns.append(line_vals[tax_group]['tax'])
            lines.append({
                'id': line_id,
                'name': iva,
                'type': 'line',
                'footnotes': context['context_id']._get_footnotes(
                    'line', line_id),
                'unfoldable': False,
                'columns': columns,
                'level': 1,
            })
            for categ_name, categ in categs_list:
                columns = []
                for base_column, tax_group in tax_group_list:
                    if base_column:
                        columns.append(
                            line_vals[tax_group]['categs'][categ]['base'])
                    columns.append(
                        line_vals[tax_group]['categs'][categ]['tax'])
                # for tax_group in tax_groups:
                #     columns += (
                #         line_vals[tax_group]['categs'][categ]['base'],
                #         line_vals[tax_group]['categs'][categ]['tax'])
                lines.append({
                    'id': line_id,
                    'name': categ_name,
                    'type': 'tax_id',
                    'footnotes': context['context_id']._get_footnotes(
                        'line', line_id),
                    'unfoldable': False,
                    'columns': columns,
                    # 'columns': [net_21, tax_21],
                    'level': 1,
                })
                line_id += 1
        return lines

    @api.model
    def get_title(self):
        return 'Reporte IVA web F2002'

    @api.model
    def get_name(self):
        return 'iva_f2002_report'

    @api.model
    def get_report_type(self):
        # return self.env.ref(
        #     'account_reports.account_report_type_no_date_range')
        return self.env.ref(
            'account_reports.account_report_type_date_range_no_comparison')
        # return self.env.ref('account_reports.account_report_type_date_range')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


class AccountReportContextTax(models.TransientModel):
    _name = "account.report.context.ret_and_perc"
    _description = "A particular context for Ret and Perc report"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.env['account.ret_and_perc.report']

    def get_columns_names(self):
        columns = [
            "Fecha", "Cuenta", "Concepto", "Comprobante", "Número"
            "Empresa", "CUIT", "Importe"
        ]
        return columns

    @api.multi
    def get_columns_types(self):
        types = [
            'text', 'text', 'text', 'text', 'text',
            'text', 'text', 'number',
        ]
        return types
