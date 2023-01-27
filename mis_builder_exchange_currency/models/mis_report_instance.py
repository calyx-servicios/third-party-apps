from odoo import api, fields, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _context_with_filters(self):
        self.ensure_one()
        context = super(MisReportInstance, self)._context_with_filters()
        context = dict(context, exchange_currency_id = self.currency_id.id)
        #se setea una variable de parametro global para setear recuperar luego la moneda definida en el reporte
        self.env['ir.config_parameter'].sudo().set_param('report_exchange_currency_id', self.currency_id.id)
        return context

