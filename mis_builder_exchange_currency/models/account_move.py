from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    exchange_currency_id = fields.Many2one('res.currency', string='Exchange Currency', compute='_get_exchange_currency')
    exchange_amount = fields.Float(string='Exchange Amount', compute='_compute_exchange_amount')

    def _get_exchange_currency(self):
        for move in self:
            #se necesita recuperar la moneda definida en el reporte en curso (seteada en la configuracion dinamica de filtros del reporte)
            report_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('report_exchange_currency_id'))
            ##############################################################
            move.exchange_currency_id = report_currency_id or move.company_id.currency_id.id

    @api.depends('exchange_currency_id')
    def _compute_exchange_amount(self):
        for move in self:
            rate = self.env['res.currency.rate'].search([('currency_id','=',move.exchange_currency_id.id),('name','<=',move.date)],order='name desc',limit=1)
            if rate:
                move.exchange_amount = move.balance * rate[0].rate
            else:
                move.exchange_amount = move.balance

