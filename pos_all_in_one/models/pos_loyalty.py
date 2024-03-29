# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError,Warning
import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
	_inherit = 'res.partner'

	loyalty_points = fields.Integer(string='Loyalty Points',compute='_compute_loyalty_points',store=True)
	loyalty_amount = fields.Float('Loyalty Amount')
	loyalty_history_ids = fields.One2many('pos.loyalty.history','partner_id',string='Loyalty history')

	@api.depends('loyalty_history_ids','loyalty_history_ids.points','loyalty_history_ids.transaction_type')
	def _compute_loyalty_points(self):
		for rec in self:
			rec.loyalty_points = 0
			for history in rec.loyalty_history_ids :
				if history.transaction_type == 'credit' :
					rec.loyalty_points += history.points
				if history.transaction_type == 'debit' :
					rec.loyalty_points -= history.points

	def action_view_loyalty_points(self):
		self.ensure_one()

		partner_loyalty_ids = self.env['pos.loyalty.history'].search([('partner_id','=',self.id)])

		return {
			'name': 'Loyalty Details',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'pos.loyalty.history',
			'domain': [('partner_id', '=', self.id)],
		}


class pos_category(models.Model):
	_inherit = 'pos.category'

	Minimum_amount  = fields.Integer("Amount For loyalty Points")
	amount_footer = fields.Integer('Amount', related='Minimum_amount')

		
class pos_loyalty_setting(models.Model):
	_name = 'pos.loyalty.setting'
	_description = "Loyalty Setting"

	name  = fields.Char('Name' ,default='Configuration for POS Loyalty Management')
	product_id  = fields.Many2one('product.product','Product', domain = [('type', '=', 'service'),('available_in_pos','=',True)])
	issue_date  =  fields.Datetime(default = datetime.now(),required=True)
	expiry_date  = fields.Datetime('Expiry date',required=True)
	issue_onlydate = fields.Date("Issue only date")
	expiry_onlydate = fields.Date("Expiry only date")
	loyalty_basis_on = fields.Selection([('amount', 'Purchase Amount'), ('pos_category', 'POS Product Categories')], string='Loyalty Basis On', help='Where you want to apply Loyalty Method in POS.')
	active  =  fields.Boolean('Active')
	loyality_amount = fields.Float('Amount')
	amount_footer = fields.Float('Amount.', related='loyality_amount')
	redeem_ids = fields.One2many('pos.redeem.rule', 'loyality_id', 'Redemption Rule')

	@api.onchange('expiry_date')
	def get_date(self):
		if self.expiry_date:
			is_dt = self.issue_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
			ex_dt = self.expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
			d1= datetime.strptime(is_dt,DEFAULT_SERVER_DATETIME_FORMAT).date()
			d2= datetime.strptime(ex_dt,DEFAULT_SERVER_DATETIME_FORMAT).date()
			self.issue_onlydate = d1
			self.expiry_onlydate = d2

	@api.constrains('issue_date','expiry_date')
	def check_date(self):
		record = self.env['pos.loyalty.setting'].search([('active','=',True)])
		for line in record:
			if line.id != self.id:
				if line.issue_date <= self.issue_date  <= line.expiry_date: 
					msg = _("You can not apply two Loyalty Configuration within same date range please change dates.")
					raise Warning(msg) 
					break
				if line.issue_date <= self.expiry_date  <= line.expiry_date:
					msg = _("You can not apply two Loyalty Configuration within same date range please change dates.")
					raise Warning(msg) 
					break

	@api.model
	def search_loyalty_product(self,product_id):
		
		product = self.product_id.search([('id','=',product_id)])

		return product.id

class pos_redeem_rule(models.Model):
	_name = 'pos.redeem.rule'    
	_description = "Loyalty Redeem Rule"

	name = fields.Char('Name' ,default='Configuration for POS Redemption Management')
	min_amt = fields.Integer('Minimum Amount')
	max_amt = fields.Integer('Maximum Amount')
	reward_amt = fields.Integer('Redemption Amount')
	loyality_id = fields.Many2one('pos.loyalty.setting', 'Loyalty ID')

	@api.onchange('max_amt','min_amt')
	def _check_amt(self):
		if (self.max_amt !=0):
			if(self.min_amt > self.max_amt):
				msg = _("Minimum Point is not larger than Maximum Point")
				raise Warning(msg) 
		return

	@api.onchange('reward_amt')
	def _check_reward_amt(self):
		if self.reward_amt !=0:
			if self.reward_amt <= 0:
				msg = _("Reward amount is not a zero or less than zero")
				raise Warning(msg) 
		return

	@api.constrains('min_amt','max_amt')
	def _check_points(self):
		for line in self:
			record = self.env['pos.redeem.rule'].search([('loyality_id','=',line.loyality_id.id)])
			for rec in record :
				if line.id != rec.id:
					if (rec.min_amt <= line.min_amt  <= rec.max_amt) or (rec.min_amt <=line.max_amt  <= rec.max_amt):
						msg = _("You can not create Redemption Rule with same points range.")
						raise Warning(msg) 
						return


class pos_loyalty_history(models.Model):
	_name = 'pos.loyalty.history'
	_rec_name = 'order_id'
	_description = "Loyalty History"
		
	order_id  = fields.Many2one('pos.order','POS Order')
	partner_id  = fields.Many2one('res.partner','Customer')
	date  =  fields.Datetime(default = datetime.now(), )
	transaction_type = fields.Selection([('credit', 'Credit'), ('debit', 'Debit')], string='Transaction Type', help='credit/debit loyalty transaction in POS.')
	points = fields.Integer('Loyalty Points')


class pos_order(models.Model):
	_inherit = 'pos.order'

	@api.model
	def create_from_ui(self, orders, draft=False):
		order_ids = super(pos_order, self).create_from_ui(orders, draft=False)
		loyalty_history_obj = self.env['pos.loyalty.history']
		today_date = datetime.today().date() 
		loyalty_setting = self.env['pos.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
							('expiry_date', '>=', today_date )])
		if loyalty_setting:
			for order_id in orders:
				if not order_id['data'].get('is_paying_partial',False):
					try:
						pos_order_id = self.search([('pos_reference','=',order_id['data'].get('name'))])
						if pos_order_id:
							ref_order = [o['data'] for o in orders if o['data'].get('name') == pos_order_id.pos_reference]
							for order in ref_order:
								cust_loyalty = pos_order_id.partner_id.loyalty_points + order.get('loyalty')
								order_loyalty = order.get('loyalty')
								redeemed = order.get('redeemed_points')
								if order_loyalty > 0:
									vals = {
										'order_id':pos_order_id.id,
										'partner_id': pos_order_id.partner_id.id,
										'date' : datetime.now(),
										'transaction_type' : 'credit',
										'points': order_loyalty
									}
									loyalty_history = loyalty_history_obj.create(vals)
								if order.get('redeem_done') == True:
									vals = {
										'order_id':pos_order_id.id,
										'partner_id': pos_order_id.partner_id.id,
										'date' : datetime.now(),
										'transaction_type' : 'debit',
										'points': redeemed
									}
									loyalty_history = loyalty_history_obj.create(vals)
							
					except Exception as e:
						_logger.error('Error in point of sale validation: %s', tools.ustr(e))
		return order_ids

	@api.model
	def get_partner_points(self, client):

		partner = self.env['res.partner'].browse(client)
		curr_loyalty_amount = partner.loyalty_points

		return curr_loyalty_amount
			
		
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    