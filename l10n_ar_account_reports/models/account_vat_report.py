# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields
# from odoo.tools.translate import _
from odoo.tools.misc import formatLang


class AccountVatReport(models.AbstractModel):
    _name = "account.vat.report"
    _description = "Libro IVA"

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        return formatLang(self.env, value, currency_obj=currency_id)

    # def _get_lines_vals(self, journal_type):

    @api.model
    def _lines(self, line_id=None):
        context = self.env.context['context_id']
        date_from = self.env.context.get('date_from')
        date_to = self.env.context.get('date_to')
        journal_type = self.env.context['journal_type']
        domain = [
            ('company_id', 'in', context.company_ids.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('journal_id.type', '=', journal_type),
        ]
        if context.journal_ids:
            domain.append(('journal_id', 'in', context.journal_ids.ids))

        recs = self.env['account.ar.vat.line'].search(domain)
        if journal_type == 'purchase':
            sign = 1.0
        else:
            sign = -1.0
        lines = []
        line_id = 0

        # puede llegar a ser mas eficiente pero es horrible, si esta en
        # el cache deberia ser igual
        # base_25 = iva_25 = base_5 = iva_5 = base_10 = iva_10 = 0.0
        # base_21 = iva_21 = base_27 = iva_27 = 0.0
        # per_iva = no_gravado_iva = otros_impuestos = total = 0.0

        for rec in recs:
            # base_25 += rec.base_25
            # iva_25 += rec.iva_25
            lines.append({
                'id': line_id,
                # 'name': rec.date,
                'name': '',
                'type': 'invoice',
                'level': 0,
                # 'type': 'line',
                # 'level': 3,
                'footnotes': context._get_footnotes('move_id', 0),
                'columns': [
                    rec.date,
                    # rec.comprobante,
                    rec.move_id.display_name,
                    rec.partner_id.name,
                    rec.partner_id.cuit,
                    rec.afip_responsability_type_id.name,
                    self._format(sign * rec.base_25),
                    self._format(sign * rec.iva_25),
                    self._format(sign * rec.base_5),
                    self._format(sign * rec.iva_5),
                    self._format(sign * rec.base_10),
                    self._format(sign * rec.iva_10),
                    self._format(sign * rec.base_21),
                    self._format(sign * rec.iva_21),
                    self._format(sign * rec.base_27),
                    self._format(sign * rec.iva_27),
                    self._format(sign * rec.per_iva),
                    self._format(sign * rec.no_gravado_iva),
                    self._format(sign * rec.otros_impuestos),
                    self._format(sign * rec.total),
                ],
            })
            line_id += 1

        lines.append({
            'id': line_id,
            'name': 'Total',
            'type': 'total',
            'footnotes': context._get_footnotes('total', 0),
            'level': 0,
            'colspan': 6,
            'columns': [
                self._format(sign * sum(recs.mapped('base_25'))),
                self._format(sign * sum(recs.mapped('iva_25'))),
                self._format(sign * sum(recs.mapped('base_5'))),
                self._format(sign * sum(recs.mapped('iva_5'))),
                self._format(sign * sum(recs.mapped('base_10'))),
                self._format(sign * sum(recs.mapped('iva_10'))),
                self._format(sign * sum(recs.mapped('base_21'))),
                self._format(sign * sum(recs.mapped('iva_21'))),
                self._format(sign * sum(recs.mapped('base_27'))),
                self._format(sign * sum(recs.mapped('iva_27'))),
                self._format(sign * sum(recs.mapped('per_iva'))),
                self._format(sign * sum(recs.mapped('no_gravado_iva'))),
                self._format(sign * sum(recs.mapped('otros_impuestos'))),
                self._format(sign * sum(recs.mapped('total'))),
            ],
        })
        return lines

    @api.model
    def get_report_type(self):
        return self.env.ref(
            'account_reports.account_report_type_date_range_no_comparison')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


class account_vat_report_purchase(models.AbstractModel):
    _name = "account.vat.report.purchase"
    _description = "Libro IVA Compras"
    _inherit = "account.vat.report"

    @api.model
    def get_title(self):
        return 'Libro IVA Compras'

    @api.model
    def get_name(self):
        return 'account_vat_report_purchase'

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env[
                'account.report.context.vat.purchase'].search(
                    [['id', '=', context_id]])
        return self.with_context(
            date_from=context_id.date_from,
            date_to=context_id.date_to,
            context_id=context_id,
            company_ids=context_id.company_ids.ids,
            journal_type='purchase',
            strict_range=True,
        )._lines(line_id=line_id)


class AccountReportContextVatPurchase(models.TransientModel):
    _name = "account.report.context.vat.purchase"
    _description = "A particular context for Libro IVA Compras"
    _inherit = "account.report.context.common"

    journal_ids = fields.Many2many(
        'account.journal', relation='account_report_ivap_journals')
    available_journal_ids = fields.Many2many(
        'account.journal', relation='account_report_ivap_available_journal',
        default=lambda s: [(6, 0, s.env['account.journal'].search(
            [('type', '=', 'purchase')]).ids)])

    @api.multi
    def get_html_and_data(self, given_context=None):
        result = super(
            AccountReportContextVatPurchase, self).get_html_and_data()
        result['report_context'].update(self.read(['journal_ids'])[0])
        result['available_journals'] = (
            self.get_available_journal_ids_names_and_codes())
        return result

    @api.multi
    def get_available_journal_ids_names_and_codes(self):
        return [[c.id, c.name, c.code] for c in self.available_journal_ids]

    def get_report_obj(self):
        return self.env['account.vat.report.purchase']

    def get_columns_names(self):
        columns = [
            "Fecha",
            # "Tipo",
            "Comprobante",
            "Proveedor", "CUIT", "Cond. IVA",
            'Grav. 2,5%', 'IVA 2,5%',
            'Grav. 5%', 'IVA 5%',
            'Grav. 10,5%', 'IVA 10,5%',
            'Grav. 21%', 'IVA 21%',
            'Grav. 27%', 'IVA 27%',
            'Perc. IVA',
            'No grav/ex',
            'Otr. Imp',
            'Total',
        ]
        return columns

    @api.multi
    def get_columns_types(self):
        types = [
            'date',
            # 'text',
            'text',
            'text', 'text', 'text',
            'number', 'number',
            'number', 'number',
            'number', 'number',
            'number', 'number',
            'number', 'number',
            'number',
            'number',
            'number',
            'number',
        ]
        return types


class account_vat_report_sale(models.AbstractModel):
    _name = "account.vat.report.sale"
    _description = "Libro IVA Ventas"
    _inherit = "account.vat.report"

    @api.model
    def get_title(self):
        return 'Libro IVA Ventas'

    @api.model
    def get_name(self):
        return 'account_vat_report_sale'

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env[
                'account.report.context.vat.purchase'].search(
                    [['id', '=', context_id]])
        return self.with_context(
            date_from=context_id.date_from,
            date_to=context_id.date_to,
            context_id=context_id,
            company_ids=context_id.company_ids.ids,
            journal_type='sale',
            strict_range=True,
        )._lines(line_id=line_id)


class AccountReportContextVatSale(models.TransientModel):
    _name = "account.report.context.vat.sale"
    _description = "A particular context for Libro IVA Compras"
    _inherit = "account.report.context.common"

    journal_ids = fields.Many2many(
        'account.journal', relation='account_report_ivas_journals')
    available_journal_ids = fields.Many2many(
        'account.journal', relation='account_report_ivas_available_journal',
        default=lambda s: [(6, 0, s.env['account.journal'].search(
            [('type', '=', 'sale')]).ids)])

    @api.multi
    def get_html_and_data(self, given_context=None):
        result = super(
            AccountReportContextVatSale, self).get_html_and_data()
        result['report_context'].update(self.read(['journal_ids'])[0])
        result['available_journals'] = (
            self.get_available_journal_ids_names_and_codes())
        return result

    @api.multi
    def get_available_journal_ids_names_and_codes(self):
        return [[c.id, c.name, c.code] for c in self.available_journal_ids]

    def get_report_obj(self):
        return self.env['account.vat.report.sale']

    def get_columns_names(self):
        columns = self.env[
            'account.report.context.vat.purchase'].get_columns_names()
        columns[2] = 'Cliente'
        return columns

    @api.multi
    def get_columns_types(self):
        return self.env[
            'account.report.context.vat.purchase'].get_columns_types()
