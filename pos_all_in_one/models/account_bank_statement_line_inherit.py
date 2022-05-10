# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import models,fields,api,_
from datetime import datetime,timedelta,date
from odoo.tools import float_is_zero


class ExchangeRate(models.Model):
	_inherit="account.bank.statement.line"

	account_currency = fields.Monetary("Amount currency")
	currency = fields.Char("currency")