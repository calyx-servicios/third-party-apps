from odoo import api, fields, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _context_with_filters(self):
        self.ensure_one()
        context = super(MisReportInstance, self)._context_with_filters()
        context = dict(context, exchange_currency_id = 2)
        self.env['account.move.line'].with_context(exchange_currency_id = 2)
        return context

