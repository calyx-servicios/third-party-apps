# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import models,fields,api,_
from datetime import datetime,timedelta,date
from odoo.tools import float_is_zero


class CurrencyInherit(models.Model):
	_inherit = "res.currency"

	rate_in_company_currency = fields.Float(compute='_compute_company_currency_rate', string='Company Currency Rate', digits=0)

	def _compute_company_currency_rate(self):
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		company_currency = company.currency_id
		for currency in self:
			price = currency.rate
			if company_currency.id != currency.id:
				new_rate = (price)/company_currency.rate
				price = round(new_rate,6)
			else:
				price = 1
			currency.rate_in_company_currency = price

class ExchangeRate(models.Model):
	_inherit="pos.payment"

	account_currency = fields.Float("Amount currency")
	currency = fields.Char("currency")

class ExchangeRate(models.Model):
	_inherit="account.bank.statement.line"

	account_currency = fields.Monetary("Amount currency")
	currency = fields.Char("currency")			


class ExchangeRate(models.Model):
	_name="currency.rate"
	_description = "Currency Rate"

	currency_id = fields.Many2one("res.currency",string="Currency")
	symbol = fields.Char(related="currency_id.symbol", string="currency symbol")
	date = fields.Datetime(string="current Date",default =datetime.today())
	rate = fields.Float(related="currency_id.rate",string="Exchange Rate")
	pos = fields.Many2one("pos.config")			