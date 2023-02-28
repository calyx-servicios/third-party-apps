# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _ , tools
from odoo.exceptions import Warning
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import random
import base64
from odoo.http import request
from functools import partial
from odoo.tools import float_is_zero
from datetime import date, datetime
from collections import defaultdict
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
import psycopg2
_logger = logging.getLogger(__name__)

class POSConfigInherit(models.Model):
	_inherit = 'pos.config'
	
	allow_partical_payment = fields.Boolean('Allow Partial Payment')
	partial_product_id = fields.Many2one("product.product",string="Partial Payment Product", domain = [('type', '=', 'service'),('available_in_pos', '=', True)])

	@api.model
	def create(self, vals):
		res=super(POSConfigInherit, self).create(vals)
		product=self.env['product.product'].browse(vals['partial_product_id'])

		if vals['allow_partical_payment']==True:
			if product:
				if product.available_in_pos != True:
					raise ValidationError(_('Please enable available in POS for the Partial Payment Product'))

				if product.taxes_id:
					raise ValidationError(_('You are not allowed to add Customer Taxes in the Partial Payment Product'))
		return res


	def write(self, vals):
		res=super(POSConfigInherit, self).write(vals)
		if self.allow_partical_payment == True:
			if self.partial_product_id.available_in_pos != True:
				raise ValidationError(_('Please enable available in POS for the Partial Payment Product'))

			if self.partial_product_id.taxes_id:
				raise ValidationError(_('You are not allowed to add Customer Taxes in the Partial Payment Product'))

		return res


class PosOrderInherit(models.Model):
	_inherit = 'pos.order'

	def _default_session(self):
		return self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

	is_partial = fields.Boolean('Is Partial Payment')
	amount_due = fields.Float("Amount Due",compute="get_amount_due")

	def get_amount_due(self):
		for order in self :
			if order.amount_paid - order.amount_total > 0:
				order.amount_due = 0
			else:
				order.amount_due = order.amount_total - order.amount_paid
				
	def write(self, vals):
		for order in self:
			if order.name == '/' and order.is_partial :
				vals['name'] = order.config_id.sequence_id._next()
		return super(PosOrderInherit, self).write(vals)

	def action_pos_order_paid(self):
		if not self.is_partial:
			return super(PosOrderInherit, self).action_pos_order_paid()
		if self.is_partial:
			if  self._is_pos_order_paid():
				self.write({'state': 'paid'})
				if self.picking_id:
					return True
				else :
					return self.create_picking()
			else:
				if not self.picking_id :
					return self.create_picking()
				else:
					return False


	@api.model
	def _order_fields(self, ui_order):
		res = super(PosOrderInherit, self)._order_fields(ui_order)
		process_line = partial(self.env['pos.order.line']._order_line_fields, session_id=ui_order['pos_session_id'])
		if 'is_partial' in ui_order:
			res['is_partial'] = ui_order['is_partial']
			res['amount_due'] = ui_order['amount_due']
		return res

	@api.model
	def _process_order(self, order, draft, existing_order):
		"""Create or update an pos.order from a given dictionary.

		:param pos_order: dictionary representing the order.
		:type pos_order: dict.
		:param draft: Indicate that the pos_order is not validated yet.
		:type draft: bool.
		:param existing_order: order to be updated or False.
		:type existing_order: pos.order.
		:returns number pos_order id
		"""
		order = order['data']
		is_partial = order.get('is_partial')
		is_draft_order = order.get('is_draft_order')
		is_paying_partial = order.get('is_paying_partial')
		pos_session = self.env['pos.session'].browse(order['pos_session_id'])
		if pos_session.state == 'closing_control' or pos_session.state == 'closed':
			order['pos_session_id'] = self._get_valid_session(order).id

		pos_order = False
		if is_paying_partial:
			pos_order = self.search([('pos_reference', '=', order.get('name'))])
		else:
			if not existing_order:
				pos_order = self.create(self._order_fields(order))
			else:
				pos_order = existing_order
				pos_order.lines.unlink()
				order['user_id'] = pos_order.user_id.id
				pos_order.write(self._order_fields(order))


		if pos_order.config_id.discount_type == 'percentage':
			pos_order.update({'discount_type': "Percentage"})
			pos_order.lines.update({'discount_line_type': "Percentage"})
		if pos_order.config_id.discount_type == 'fixed':
			pos_order.update({'discount_type': "Fixed"})
			pos_order.lines.update({'discount_line_type': "Fixed"})
		coupon_id = order.get('coupon_id', False)
		coup_max_amount = order.get('coup_maxamount',False)
		pos_order.write({'coupon_id':  coupon_id})
		pos_order.coupon_id.update({'coupon_count': pos_order.coupon_id.coupon_count + 1})
		pos_order.coupon_id.update({'max_amount': coup_max_amount})
		self._process_payment_lines(order, pos_order, pos_session, draft)

		try:
			pos_order.action_pos_order_paid()
		except psycopg2.DatabaseError:
			# do not hide transactional errors, the order(s) won't be saved!
			raise
		except Exception as e:
			_logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
		if order.get('to_invoice' , False) and pos_order.state == 'paid':
			pos_order.action_pos_order_invoice()
			if pos_order.discount_type and pos_order.discount_type == "Fixed":
				invoice = pos_order.account_move
				for line in invoice.invoice_line_ids : 
					pos_line = line.pos_order_line_id
					if pos_line and pos_line.discount_line_type == "Fixed":
						line.write({'price_unit':pos_line.price_unit})

		return pos_order.id


class PosSessionInherit(models.Model):
	_inherit = 'pos.session'

	@api.model
	def create(self, vals):
		res = super(PosSessionInherit, self).create(vals)
		orders = self.env['pos.order'].search([('user_id', '=', request.env.uid),
			('state', '=', 'draft'),('session_id.state', '=', 'closed')])
		orders.write({'session_id': res.id})
		return res

	def _validate_session(self):
		self.ensure_one()
		if self.state == 'closed':
			raise UserError(_('This session is already closed.'))
			
		draft_orders = self.order_ids.filtered(lambda order: order.state == 'draft')
		do = []
		for i in draft_orders:
			if not i.is_partial :
				do.append(i.name)
		if do:
			raise UserError(_(
					'There are still orders in draft state in the session. '
					'Pay or cancel the following orders to validate the session:\n%s'
				) % ', '.join(do)
			)
		else:
			# Users without any accounting rights won't be able to create the journal entry. If this
			# case, switch to sudo for creation and posting.
			sudo = False
			if (
				not self.env['account.move'].check_access_rights('create', raise_exception=False)
				and self.user_has_groups('point_of_sale.group_pos_user')
			):
				sudo = True
				self.sudo()._create_account_move()
			else:
				self._create_account_move()
			if self.move_id.line_ids:
				self.move_id.post() if not sudo else self.move_id.sudo().post()
				# Set the uninvoiced orders' state to 'done'
				self.env['pos.order'].search([('session_id', '=', self.id), ('state', '=', 'paid')]).write({'state': 'done'})
			else:
				# The cash register needs to be confirmed for cash diffs
				# made thru cash in/out when sesion is in cash_control.
				if self.config_id.cash_control:
					self.cash_register_id.button_confirm_bank()
				self.move_id.unlink()
			self.write({'state': 'closed'})
			return {
				'type': 'ir.actions.client',
				'name': 'Point of Sale Menu',
				'tag': 'reload',
				'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
			}

	def _accumulate_amounts(self, data):
		# Accumulate the amounts for each accounting lines group
		# Each dict maps `key` -> `amounts`, where `key` is the group key.
		# E.g. `combine_receivables` is derived from pos.payment records
		# in the self.order_ids with group key of the `payment_method_id`
		# field of the pos.payment record.
		amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
		tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
		split_receivables = defaultdict(amounts)
		split_receivables_cash = defaultdict(amounts)
		combine_receivables = defaultdict(amounts)
		combine_receivables_cash = defaultdict(amounts)
		invoice_receivables = defaultdict(amounts)
		sales = defaultdict(amounts)
		taxes = defaultdict(tax_amounts)
		stock_expense = defaultdict(amounts)
		stock_output = defaultdict(amounts)
		# Track the receivable lines of the invoiced orders' account moves for reconciliation
		# These receivable lines are reconciled to the corresponding invoice receivable lines
		# of this session's move_id.
		order_account_move_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
		rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
		order_ids = self.order_ids.filtered(lambda order: order.is_partial == False)
		for order in order_ids:
			# Combine pos receivable lines
			# Separate cash payments for cash reconciliation later.
			for payment in order.payment_ids:
				amount, date = payment.amount, payment.payment_date
				if payment.payment_method_id.split_transactions:
					if payment.payment_method_id.is_cash_count:
						split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
					else:
						split_receivables[payment] = self._update_amounts(split_receivables[payment], {'amount': amount}, date)
				else:
					key = payment.payment_method_id
					if payment.payment_method_id.is_cash_count:
						combine_receivables_cash[key] = self._update_amounts(combine_receivables_cash[key], {'amount': amount}, date)
					else:
						combine_receivables[key] = self._update_amounts(combine_receivables[key], {'amount': amount}, date)

			if order.is_invoiced:
				# Combine invoice receivable lines
				key = order.partner_id
				invoice_receivables[key] = self._update_amounts(invoice_receivables[key], {'amount': order._get_amount_receivable()}, order.date_order)
				# side loop to gather receivable lines by account for reconciliation
				for move_line in order.account_move.line_ids.filtered(lambda aml: aml.account_id.internal_type == 'receivable' and not aml.reconciled):
					order_account_move_receivable_lines[move_line.account_id.id] |= move_line
			else:
				order_taxes = defaultdict(tax_amounts)
				for order_line in order.lines:
					line = self._prepare_line(order_line)
					# Combine sales/refund lines
					sale_key = (
						# account
						line['income_account_id'],
						# sign
						-1 if line['amount'] < 0 else 1,
						# for taxes
						tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
						line.get('base_tags',tuple()),
					)
					sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
					# Combine tax lines
					for tax in line['taxes']:
						tax_key = (tax['account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
						order_taxes[tax_key] = self._update_amounts(
							order_taxes[tax_key],
							{'amount': tax['amount'], 'base_amount': tax['base']},
							tax['date_order'],
							round=not rounded_globally
						)
				for tax_key, amounts in order_taxes.items():
					if rounded_globally:
						amounts = self._round_amounts(amounts)
					for amount_key, amount in amounts.items():
						taxes[tax_key][amount_key] += amount

				if self.company_id.anglo_saxon_accounting and order.picking_id.id:
					# Combine stock lines
					order_pickings = self.env['stock.picking'].search([
						'|',
						('origin', '=', '%s - %s' % (self.name, order.name)),
						('id', '=', order.picking_id.id)
					])
					stock_moves = self.env['stock.move'].search([
						('picking_id', 'in', order_pickings.ids),
						('company_id.anglo_saxon_accounting', '=', True),
						('product_id.categ_id.property_valuation', '=', 'real_time')
					])
					for move in stock_moves:
						exp_key = move.product_id.property_account_expense_id or move.product_id.categ_id.property_account_expense_categ_id
						out_key = move.product_id.categ_id.property_stock_account_output_categ_id
						amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
						stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
						stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

				# Increasing current partner's customer_rank
				partners = (order.partner_id | order.partner_id.commercial_partner_id)
				partners._increase_rank('customer_rank')

		MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

		data.update({
			'taxes':                               taxes,
			'sales':                               sales,
			'stock_expense':                       stock_expense,
			'split_receivables':                   split_receivables,
			'combine_receivables':                 combine_receivables,
			'split_receivables_cash':              split_receivables_cash,
			'combine_receivables_cash':            combine_receivables_cash,
			'invoice_receivables':                 invoice_receivables,
			'stock_output':                        stock_output,
			'order_account_move_receivable_lines': order_account_move_receivable_lines,
			'MoveLine':                            MoveLine
		})
		return data

