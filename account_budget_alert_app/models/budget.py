# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class BudgetLines(models.Model):
	_inherit = 'crossovered.budget.lines'


	allow2_manager = fields.Boolean("Allow to Maanger")
	warning_type = fields.Selection([('ignore', 'Ignore'),('warning','Warning'),('restrict','Restriction')])
	is_active = fields.Boolean("Active")


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	exceed_note = fields.Char("Warning Info", default="")
	is_warning  = fields.Boolean()

	def button_confirm(self):
		for record in self:
			today = record.date_order
			budget_ids = self.env['crossovered.budget'].search([
				('state','not in',['draft','cancel','done']),
				('date_from','<=',today),
				('date_to','>=',today)])
			if budget_ids:
				for budget in budget_ids:
					pname = []
					ppname = []
					flag = False 
					flag_w = False
					for bline in budget.crossovered_budget_line.filtered(lambda bline: bline.is_active == True):
						if self.order_line:						
							for pline in self.order_line:
								if bline.warning_type == 'warning' and bline.analytic_account_id == pline.account_analytic_id and pline.price_subtotal >= (bline.planned_amount - abs(bline.practical_amount)):
									if  pline.product_id.name not in pname:
										pname.append(pline.product_id.name)
									self.is_warning = True
									flag_w = True

								if bline.warning_type == 'restrict' and bline.analytic_account_id == pline.account_analytic_id and pline.price_subtotal >= (bline.planned_amount - abs(bline.practical_amount)) and not bline.allow2_manager:
									if pline.product_id.name not in ppname:
										ppname.append(pline.product_id.name)
									flag = True

								if bline.warning_type == 'restrict' and bline.allow2_manager and self.env.user.has_group('account.group_account_manager'):
									self.is_warning = True
									self.exceed_note = "Order amount exceeed than budget amount, but allow manager can also confirm order"

								if bline.warning_type == 'ignore':
									self.is_warning = True
									self.exceed_note = "Successfully confirmed Purchse order then proceed"
					if flag:
						raise ValidationError(_("Restriction on Confirm Purchase Order : Budget Limit exceeding on %s Product")% str(ppname))
					if flag_w:
						self.exceed_note = "Budget Limit exceeding on "+str(pname)+" products."
		res = super(PurchaseOrder,self).button_confirm()
		return res


class AccountMove(models.Model):
	_inherit = 'account.move'

	exceed_note = fields.Char("Warning Info", default="")
	is_warning  = fields.Boolean()


	def action_post(self):
		for record in self:
			today = record.invoice_date
			budget_ids = self.env['crossovered.budget'].search([
				('state','not in',['draft','cancel','done']),
				('date_from','<=',today),
				('date_to','>=',today)])
			if budget_ids:
				for budget in budget_ids:
					acc_name = []
					acc_name_res = []
					flag = False 
					flag_w = False

					for bline in budget.crossovered_budget_line.filtered(lambda bline: bline.is_active == True):
						if self.invoice_line_ids:
							for iline in self.invoice_line_ids:
								if bline.warning_type == 'warning' and bline.analytic_account_id == iline.analytic_account_id and iline.price_subtotal >= (bline.planned_amount - abs(bline.practical_amount)):
									if iline.account_id.name not in acc_name:
										acc_name.append(iline.account_id.name)

									self.is_warning = True
									flag_w = True
								
								if bline.warning_type == 'restrict' and bline.analytic_account_id == iline.analytic_account_id and iline.price_subtotal >= (bline.planned_amount - abs(bline.practical_amount)) and not bline.allow2_manager:
									if iline.account_id.name not in acc_name_res:
										acc_name_res.append(iline.account_id.name)
									flag = True


								if bline.warning_type == 'restrict' and bline.allow2_manager:
									self.is_warning = True
									self.exceed_note = "Budget limit exceed, but allow manager can validate Vendor Bill"


								if bline.warning_type == 'ignore':
									self.is_warning = True
									self.exceed_note = "Successfully confirmed Vendor Bills then proceed"
					
					if flag:
						raise ValidationError(_("Restriction on Validate Bill : Budget Limit exceeding on %s Account")% str(acc_name_res))
					if flag_w and self.is_warning:
						self.exceed_note = "Budget Limit exceeding for "+str(acc_name)+" Account."

		res = super(AccountMove,self).action_post()
		return res
