# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api
# from odoo.tools.translate import _
from odoo.tools.misc import formatLang
import logging
_logger = logging.getLogger(__name__)


class AccountIvaF2002Report(models.AbstractModel):
    _name = "account.iva_f2002.report"
    _description = "IVA F2002 Tax Report"

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
            context_id=context_id,
            company_ids=context_id.company_ids.ids,
            # es para que el query de los moves no traiga todo lo anterior
            strict_range=True,
            state=context_id.all_entries and 'all' or 'posted',
        )._lines()

    @api.model
    def _prepare_line(self, lines_vals, title, type, columns, level):
        columnes_qty = 4
        context = self.env.context['context_id']
        line_id = lines_vals['last_line_id'] + 1
        lines_vals['last_line_id'] = line_id
        return {
            'id': line_id,
            'name': title,
            'type': type,
            'footnotes': context._get_footnotes(type, line_id),
            'unfoldable': False,
            'columns': columns,
            'colspan': columnes_qty - len(columns),
            'level': level,
        }

    @api.model
    # def _add_line(self, lines_vals, title, type, columns, level):
    def _add_line(self, lines_vals, vals):
        lines_vals['lines'].append(vals)

    @api.model
    def _add_alicuot_lines(
            self,
            lines_vals,
            tax_groups,
            sign,
            afip_responsabilities=None,
            f2002_category=None,
            activity=None,
            type_tax_use=None,
            credit_or_debit=None,
            domain=None):
        date_from = self.env.context.get('date_from')
        date_to = self.env.context.get('date_to')
        company_ids = self.env.context.get('company_ids')
        # tg_nc = ref('l10n_ar_account.tax_group_iva_no_corresponde', False)
        # tg_ng = ref('l10n_ar_account.tax_group_iva_no_gravado', False)
        # tg_ex = ref('l10n_ar_account.tax_group_iva_exento', False)
        # tg_0 = ref('l10n_ar_account.tax_group_iva_0', False)
        tax_count = 0
        total_base = 0.0
        total_vat = 0.0
        total_total = 0.0
        for tax_group, perc in tax_groups:
            line_domain = self.env[
                'account.move.line']._get_tax_move_lines_domain(
                    date_from, date_to, 'base',
                    tax_groups=tax_group,
                    # document_types=document_types,
                    afip_responsabilities=afip_responsabilities,
                    f2002_category=f2002_category,
                    activity=activity,
                    type_tax_use=type_tax_use,
                    credit_or_debit=credit_or_debit,
                    company_ids=company_ids,
                    domain=domain,
            )
            amount = self.env['account.move.line'].\
                read_group(line_domain, ['balance'], [])[0]['balance']
            _logger.debug('Amount %s' % amount)
            if not amount:
                continue
            base = sign * amount
            vat = base * perc / 100.0
            total = base * (1 + perc / 100.0)
            total_base += base
            total_vat += vat
            total_total += total

            tax_count += 1
            columns = [
                self._format(base),
                self._format(vat),
                self._format(total),
            ]
            title = tax_group.name
            vals = self._prepare_line(
                lines_vals, title, 'alicuot', columns, 1)
            vals['action_name'] = title
            vals['domain'] = line_domain
            self._add_line(lines_vals, vals)

        # if tax count is 0, no line added
        if tax_count == 0:
            return True
        lines_vals['base'] += total_base
        lines_vals['vat'] += total_vat
        lines_vals['total'] += total_total
        columns = [
            self._format(total_base),
            self._format(total_vat),
            self._format(total_total),
        ]
        self._add_line(
            lines_vals, self._prepare_line(
                lines_vals, 'Total', 'o_account_reports_domain_total',
                columns, 1))

    @api.model
    def _lines(self):
        # preparado de valores
        context = self.env.context['context_id']
        # date_from = context.get('date_from')
        # date_to = context.get('date_to')

        ref = self.env.ref
        tg_25 = ref('l10n_ar_account.tax_group_iva_25', False)
        tg_5 = ref('l10n_ar_account.tax_group_iva_5', False)
        tg_10 = ref('l10n_ar_account.tax_group_iva_10', False)
        tg_21 = ref('l10n_ar_account.tax_group_iva_21', False)
        tg_27 = ref('l10n_ar_account.tax_group_iva_27', False)
        tg_nc = ref('l10n_ar_account.tax_group_iva_no_corresponde', False)
        tg_ng = ref('l10n_ar_account.tax_group_iva_no_gravado', False)
        tg_ex = ref('l10n_ar_account.tax_group_iva_exento', False)
        tg_0 = ref('l10n_ar_account.tax_group_iva_0', False)
        # con vat_tax_groups referimos a != iva 0
        # pasamos los porcentajes para estimar un iva y un monto total
        # ya que las lineas de iva estan agrupadas y no sabemos cuando se
        # corresponde con cada actividad o producto
        vat_tax_groups = [
            (tg_25, 2.5), (tg_5, 5.0), (tg_10, 10.5),
            (tg_21, 21.0), (tg_27, 27.0)]
        vat0_tax_groups = [
            (tg_nc, 0.0), (tg_ng, 0.0), (tg_ex, 0.0), (tg_0, 0.0)]

        # para activities y categs agregamos una vacia al principio para
        # representar sin categoria
        activities = context.company_ids.mapped(
            'partner_id.actividades_padron')
        act_list = [activities.browse()] + [x for x in activities]

        categs = self.env['afip.vat.f2002_category'].search([])
        categ_list = [categs.browse()] + [x for x in categs]

        ref = self.env.ref
        res_IVARI = ref('l10n_ar_account.res_IVARI')
        res_IVARIFM = ref('l10n_ar_account.res_IVARIFM')
        res_IVARI_AP = ref('l10n_ar_account.res_IVARI_AP')
        res_IVANR = ref('l10n_ar_account.res_IVANR')
        res_IVAE = ref('l10n_ar_account.res_IVAE')
        res_CF = ref('l10n_ar_account.res_CF')
        res_RM = ref('l10n_ar_account.res_RM')
        res_NOCATEG = ref('l10n_ar_account.res_NOCATEG')
        res_EXT = ref('l10n_ar_account.res_EXT')
        res_CLI_EXT = ref('l10n_ar_account.res_CLI_EXT')
        res_IVA_LIB = ref('l10n_ar_account.res_IVA_LIB')
        res_EVENTUAL = ref('l10n_ar_account.res_EVENTUAL')
        res_MON_SOCIAL = ref('l10n_ar_account.res_MON_SOCIAL')
        res_EVENTUAL_SOCIAL = ref('l10n_ar_account.res_EVENTUAL_SOCIAL')

        resp_insc = res_IVARI + res_IVARIFM + res_IVARI_AP
        cf_ex_na = res_IVANR + res_IVAE + res_CF
        mono = res_MON_SOCIAL + res_RM
        otros_conc = res_NOCATEG + res_EVENTUAL_SOCIAL + res_EVENTUAL
        op_ng_ex = res_CLI_EXT + res_IVA_LIB + res_EXT

        ########################
        # construccion de lineas
        ########################

        # lines = []
        res = {
            'lines': [], 'last_line_id': 0,
            'base': 0.0, 'vat': 0.0, 'total': 0.0}

        # debito fiscal por actividad
        #############################
        for activity in act_list:
            # venta cosas muebles y loca...
            ###############################
            title = (
                "Operaciones de venta de cosas muebles, obras, locaciones y/o "
                "prestaciones de servicios")
            self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
            # detalle por responsabilidad
            income_type = ref('account.data_account_type_revenue')
            detail_by_resp = [
                ('Responsables Inscriptos', resp_insc),
                ('Consumidores finales, Exentos y No alcanzados', cf_ex_na),
                ('Operaciones con Monotributistas - Régimen Simplificado',
                    mono),
                ('Otros conceptos', otros_conc),
                ('Operaciones no gravadas y exentas', op_ng_ex),
            ]
            for title, resps in detail_by_resp:
                self._add_line(
                    res, self._prepare_line(res, title, 'line', [], 2))

                self._add_alicuot_lines(
                    res,
                    vat_tax_groups,
                    -1.0,
                    activity=activity,
                    afip_responsabilities=resps,
                    type_tax_use='sale',
                    credit_or_debit='credit',
                    domain=[('account_id.user_type_id', '=', income_type.id)],
                )

            # venta bienes de uso
            #####################
            title = ("Operaciones de venta de bienes de uso")
            self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
            # detalle por responsabilidad
            detail_by_resp = [
                ('Responsables Inscriptos', resp_insc),
                ('Consumidores finales, Monotributistas, Exentos y No '
                    'alcanzados', (
                        cf_ex_na + mono + otros_conc + op_ng_ex)),
            ]
            for title, resps in detail_by_resp:
                self._add_line(
                    res, self._prepare_line(res, title, 'line', [], 2))
                self._add_alicuot_lines(
                    res,
                    vat_tax_groups,
                    -1.0,
                    activity=activity,
                    afip_responsabilities=resps,
                    type_tax_use='sale',
                    credit_or_debit='credit',
                    domain=[('account_id.user_type_id', '!=', income_type.id)])
                columns = [
                    self._format(res['base']),
                    self._format(res['vat']),
                    self._format(res['total']),
                ]
            title = "Total Débito fiscal - %s" % (
                activity and activity.name or 'Sin Actividad')
            columns = [
                self._format(res['base']),
                self._format(res['vat']),
                self._format(res['total']),
            ]
            res['total'] = res['vat'] = res['base'] = 0.0
            self._add_line(res, self._prepare_line(
                res, title, 'line', columns, 0))

        # restitucion credito fiscal
        ############################
        title = "Crédito fiscal a Restituir"
        self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
        for categ in categ_list:
            title = categ and categ.name or 'Sin Categoría'
            self._add_line(
                res, self._prepare_line(res, title, 'line', [], 2))
            # lines.append(self._get_lines_vals(line_id, title, 'line', [], 3))
            self._add_alicuot_lines(
                res,
                vat_tax_groups,
                -1.0,
                f2002_category=categ,
                type_tax_use='purchase',
                credit_or_debit='credit',
            )
        columns = [
            self._format(res['base']),
            self._format(res['vat']),
            self._format(res['total']),
        ]
        res['total'] = res['vat'] = res['base'] = 0.0
        title = "Total Crédito fiscal a Restituir"
        self._add_line(res, self._prepare_line(res, title, 'line', columns, 0))

        ################
        # credito fiscal
        ################

        # compra cosas muebles y loca...
        ################################
        title = (
            "Operaciones de compra de cosas muebles, obras, locaciones y/o "
            "prestaciones de servicios")
        self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
        for categ in categ_list:
            title = categ and categ.name or 'Sin Categoría'
            self._add_line(
                res, self._prepare_line(res, title, 'line', [], 2))
            self._add_alicuot_lines(
                res,
                vat_tax_groups,
                1.0,
                f2002_category=categ,
                type_tax_use='purchase',
                credit_or_debit='debit',
            )
        columns = [
            self._format(res['base']),
            self._format(res['vat']),
            self._format(res['total']),
        ]
        res['total'] = res['vat'] = res['base'] = 0.0
        title = (
            "Total Crédito por operaciones de compra de cosas muebles, obras, "
            "locaciones y/o prestaciones de servicios de compra...")
        self._add_line(res, self._prepare_line(res, title, 'line', columns, 0))

        # Operaciones que no generan crédito fiscal
        ###########################################
        title = "Operaciones que no generan crédito fiscal"
        self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
        detail_by_resp = [
            ('Sujetos Exentos, No Alcanzados, Monotributistas y Consumidores '
                'Finales', (
                    cf_ex_na + mono + otros_conc + op_ng_ex)),
            ('Otras compras que no generan Crédito Fiscal', resp_insc),
        ]
        for title, resps in detail_by_resp:
            self._add_line(res, self._prepare_line(res, title, 'line', [], 2))
            self._add_alicuot_lines(
                res,
                vat0_tax_groups,
                1.0,
                afip_responsabilities=resps,
                type_tax_use='purchase',
                credit_or_debit='debit',
            )
        columns = [
            self._format(res['base']),
            self._format(res['vat']),
            self._format(res['total']),
        ]
        res['total'] = res['vat'] = res['base'] = 0.0
        title = "Total Operaciones que no generan crédito fiscal"
        self._add_line(res, self._prepare_line(res, title, 'line', columns, 0))

        # restitucion debito fiscal
        ############################
        title = "Débito fiscal a resituir"
        self._add_line(res, self._prepare_line(res, title, 'line', [], 1))
        detail_by_resp = [
            ('Responsables Inscriptos', resp_insc),
            ('Sujetos Exentos, No Alcanzados, Monotributistas y Consumidores '
                'Finales', (
                    cf_ex_na + mono + otros_conc + op_ng_ex)),
        ]
        for title, resps in detail_by_resp:
            self._add_line(res, self._prepare_line(res, title, 'line', [], 2))
            self._add_alicuot_lines(
                res,
                vat_tax_groups,
                1.0,
                afip_responsabilities=resps,
                type_tax_use='sale',
                credit_or_debit='debit',
            )
        columns = [
            self._format(res['base']),
            self._format(res['vat']),
            self._format(res['total']),
        ]
        title = "Total Débito fiscal a resituir"
        self._add_line(res, self._prepare_line(res, title, 'line', columns, 0))

        return res['lines']

    @api.model
    def get_title(self):
        return 'Reporte IVA web F2002'

    @api.model
    def get_name(self):
        return 'iva_f2002_report'

    @api.model
    def get_report_type(self):
        return self.env.ref(
            'account_reports.account_report_type_date_range_no_comparison')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'

    @api.model
    def get_tax_group_list(self):
        ref = self.env.ref
        return [
            (True, ref('l10n_ar_account.tax_group_iva_21')),
            (True, ref('l10n_ar_account.tax_group_iva_10')),
            (False, ref('l10n_ar_account.tax_group_percepcion_iva')),
        ]


class AccountReportContextTax(models.TransientModel):
    _name = "account.report.context.iva_f2002"
    _description = "A particular context for IVA f2002 report"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.env['account.iva_f2002.report']

    def get_columns_names(self):
        columns = [
            "Neto Gravado",
            "IVA",
            # "Crédito Fiscal Facturado",
            "Total Facturado",
        ]

        return columns

    @api.multi
    def get_columns_types(self):
        types = [
            'number',
            'number',
            'number',
        ]
        return types
