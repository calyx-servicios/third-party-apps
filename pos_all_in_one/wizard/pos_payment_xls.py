# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
import xlwt
from odoo.exceptions import Warning
from datetime import datetime
from odoo import tools
from xlwt import easyxf
import math
import io
import logging
_logger = logging.getLogger(__name__)

try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')


class sales_report_wizard(models.TransientModel):
	_name = 'report.wizard'
	_description ="POS report Wizard"

	
	start_date = fields.Date('Start Date', required=True)
	end_date = fields.Date('End Date', required=True)



	def generate_report(self):
		data = {'date_start': self.start_date, 'date_stop': self.end_date,}
		return self.env.ref('bi_sales_pos_invoice_report.sale_daily_report').report_action(self,data=data)


	def print_excel_report(self):           
			import base64
			filename = 'Sales_POS_Invoice123.xls'
			workbook = xlwt.Workbook()
			style = xlwt.XFStyle()
			tall_style = xlwt.easyxf('font:height 720;') # 36pt
			worksheet = workbook.add_sheet('Sheet 1')
			num_style = easyxf(num_format_str='#,##0')
			num_bold =  easyxf('font:bold on',num_format_str='#,##0', )            
			heading_style = easyxf('font:name Arial, bold on,height 350, color  dark_green; align: vert centre, horz center ;')            
			first_col = worksheet.col(0)
			first_col.width = 256 *30
			second_col = worksheet.col(1)
			second_col.width = 256 *20
			three_col = worksheet.col(2)
			three_col.width = 256 *20
			four_col = worksheet.col(5)
			four_col.width = 256 *30
			five_col = worksheet.col(7)
			five_col.width = 256 *20
			small_heading_style  =  easyxf('font:  name  Century Gothic, bold on, color white , height 230 ; pattern: pattern solid,fore-colour dark_green; align: vert centre, horz center ;')
			medium_heading_style = easyxf('font:name Arial, bold on,height 250, color  dark_green; align: vert centre, horz center ;')
			bold = easyxf('font: bold on ')
			duration  = 'From:'  + str(self.start_date) + '   ' + 'To:'   + str(self.end_date)
			worksheet.write_merge(0, 4, 0, 10, 'Detailed Product Sales Report' + ' ' + duration, heading_style)
			worksheet.write_merge(5,5,0,3,  'POS Products Details', medium_heading_style)
			worksheet.write(6, 0, 'POS Products', small_heading_style)
			worksheet.write(6, 1, 'Quantity', small_heading_style)
			worksheet.write(6, 2, 'Price/Unit', small_heading_style)     
			worksheet.write(6, 3, 'Total', small_heading_style)
			worksheet.write_merge(5,5, 5,8, 'Sales Products Details', medium_heading_style)
			worksheet.write(6, 5, 'Products', small_heading_style)
			worksheet.write(6, 6, 'Quantity', small_heading_style)
			worksheet.write(6, 7, 'Price/Unit', small_heading_style)     
			worksheet.write(6, 8, 'Total', small_heading_style)
			#pos order 
			pos_orders = self.env['pos.order'].search([('date_order','>=',self.start_date ) , ('date_order','<=', self.end_date ), ('state', 'in', ['paid','invoiced','done'])])
			sales_order = self.env['sale.order'].search([('state', 'in', ['sale','done']),('date_order','>=',self.start_date ) , ('date_order','<=', self.end_date )])
			products_sale_sold = {}
			for order in sales_order:
				for line in order.order_line:
					key = (line.product_id, line.price_unit, line.discount)
					products_sale_sold.setdefault(key, 0.0)
					products_sale_sold[key] += line.product_uom_qty
			sales_data = {'products': sorted([{
				'product_id': product.id,
				'product_name': product.name,
				'code': product.default_code,
				'quantity': qty,
				'price_unit': price_unit,
				'discount': discount,
				'uom': product.uom_id.name
			} for (product, price_unit, discount), qty in products_sale_sold.items()], key=lambda l: l['product_name'])}
			pos_order_ids  = []
			for pos_order_obj  in pos_orders:
				pos_order_ids.append(pos_order_obj.id)
			r = 7
			total = 0
			order_lines = []
			products_sold = {}
			taxes = {}
			data  = {}
			user_currency = self.env.user.company_id.currency_id
			for order in pos_orders:
				if user_currency != order.pricelist_id.currency_id:
					total += order.pricelist_id.currency_id.compute(order.amount_total, user_currency)
				else:
					total += order.amount_total
				currency = order.session_id.currency_id
				for line in order.lines:
					key = (line.product_id, line.price_unit, line.discount)
					products_sold.setdefault(key, 0.0)
					products_sold[key] += line.qty
					if line.tax_ids_after_fiscal_position:
						 line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
						 for tax in line_taxes['taxes']:
							 taxes.setdefault(tax['id'], {'name': tax['name'], 'total':0.0})
							 taxes[tax['id']]['total'] += tax['amount']
			data = {'products': sorted([{
				'product_id': product.id,
				'product_name': product.name,
				'code': product.default_code,
				'quantity': qty,
				'price_unit': price_unit,
				'discount': discount,
				'uom': product.uom_id.name
			} for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])}
			st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', pos_orders.ids)]).ids
			if st_line_ids:
				self.env.cr.execute("""
				SELECT aj.name, sum(amount) total
				FROM account_bank_statement_line AS absl,
					 account_bank_statement AS abs,
					 account_journal AS aj 
				WHERE absl.statement_id = abs.id
					AND abs.journal_id = aj.id 
					AND absl.id IN %s 
				GROUP BY aj.name
			""", (tuple(st_line_ids),))
				payments = self.env.cr.dictfetchall()
			else:
				payments = []
			total = 0
			p_qty   = 0 
			for product_details in data.get('products') : 
						r =r  +1
						worksheet.write(r, 0, product_details.get('product_name') )
						worksheet.write(r, 1, int(product_details.get('quantity')), num_style )
						worksheet.write(r, 2, int(product_details.get('price_unit')), num_style)
						worksheet.write(r, 3, int(product_details.get('quantity') * product_details.get('price_unit')), num_style)
						p_qty =  p_qty   + product_details.get('quantity') 
						total = total  + product_details.get('quantity') * product_details.get('price_unit')                 
			worksheet.write(r+1, 1, int(p_qty), num_bold)
			worksheet.write(r+1, 3, int(total) , num_bold )
			st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', pos_order_ids)]).ids
			if st_line_ids:
				self.env.cr.execute("""
				SELECT aj.name, sum(amount) total
				FROM account_bank_statement_line AS absl,
					 account_bank_statement AS abs,
					 account_journal AS aj 
				WHERE absl.statement_id = abs.id
					AND abs.journal_id = aj.id 
					AND absl.id IN %s 
				GROUP BY aj.name
			""", (tuple(st_line_ids),))
			payments = self.env.cr.dictfetchall()
			total2 = 0
			r2 = 7
			s_qty = 0
			for sales_data in sales_data.get('products'):                    
					r2 = r2 +1
					worksheet.write(r2, 5, sales_data.get('product_name') )
					worksheet.write(r2, 6, int(sales_data.get('quantity')) ,num_style  )
					worksheet.write(r2, 7, int(sales_data.get('price_unit')),num_style  )
					worksheet.write(r2, 8, int( sales_data.get('quantity') * sales_data.get('price_unit')), num_style)
					total2 = total2  + (sales_data.get('quantity') * sales_data.get('price_unit'))
					s_qty  =  s_qty +  sales_data.get('quantity')                    
			worksheet.write(r2+1, 6, int(s_qty), num_bold)
			worksheet.write(r2+1, 8, int(total2), num_bold)
			sql  = ("SELECT aj.name, sum(amount) total " + " "
				  "FROM account_payment AS absl,"
				  "account_journal AS aj " + ""
				  "where" + " "+
				  "absl.journal_id = aj.id" + " " +
				  "and absl.name ilike "+ " " +"'cust%%'" +  " "+
				  "and absl.payment_date >= %s" + " " +
				  "and absl.payment_date <= %s"+ " "+
				  "GROUP BY aj.name"
				   )
			self._cr.execute(sql ,(self.start_date, self.end_date))
			tot = 0              
			if r+1 > r2+1:
			   r =r+2 
			else:
			  r = r2 +2
			total_data = self.env.cr.dictfetchall()
			worksheet.write_merge(r,r+1,0,10, 'Payments Received in the Period', heading_style)
			worksheet.write_merge(r+2, r+2,0 ,1 ,'POS', small_heading_style)
			worksheet.write_merge(r+2, r+2,2 ,3 ,'Invoice', small_heading_style)
			r =  r+ 2
			main_row  =r 
			tp = 0
			for payment in payments:
				r = r + 1                
				worksheet.write(r, 0, payment.get('name'))
				worksheet.write(r, 1, int(payment.get('total')), num_style)
				tp =  tp  + payment.get('total')
			ti = 0
			r2 = main_row
			if total_data:
				for payment in total_data:
					r2 = r2 + 1
					ti  =  ti  + payment.get('total')
					worksheet.write(r2, 2, payment.get('name'))
					worksheet.write(r2, 3, payment.get('total'), num_style)
			if r2 > r:
			   r =r2
			else:
				r =r 
			worksheet.write(r+1, 0 ,'Total', small_heading_style)   
			worksheet.write(r+1, 1 ,int(tp), num_bold)
			worksheet.write(r+1, 3 ,int(ti), num_bold)
			worksheet.write_merge(r+3,r+4,0,10, 'Customer Invoices Raised in the Period', heading_style)
			worksheet.write(r+5 , 1,'Paid',   small_heading_style)
			worksheet.write(r+5 , 2,'Unpaid', small_heading_style)
			worksheet.write(r+5 , 3,'Total',  small_heading_style)
			sql  = ("select sum(amount_total),state from account_invoice where type='out_invoice' and create_date >= %s and create_date <= %s group by state")
			self._cr.execute(sql, (self.start_date, self.end_date))             
			last_data = self.env.cr.dictfetchall()
			total = 0 
			paid  = 0.0
			for data in last_data: 
				total = total + data.get('sum')
				if data.get('state') == 'paid':
				   paid  = data.get('sum')
			worksheet.write(r+6 , 0,'Amount', bold)
			worksheet.write(r+6 , 1, int(paid), num_bold)
			worksheet.write(r+6 , 2, int(total-paid), num_bold) 
			worksheet.write(r+6 , 3, int(total), num_bold)
			fp = io.BytesIO()        
			workbook.save(fp)
			export_id = self.env['sale.excel.report'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
			fp.close()
			return {
				'view_mode': 'form',
				'res_id': export_id.id,
				'res_model': 'sale.excel.report',
				'view_type': 'form',
				'type': 'ir.actions.act_window',
				'target': 'new',
			}
			return True
			
class sale_excel_report(models.TransientModel):
	_name= "sale.excel.report"
	
	excel_file = fields.Binary('Sales Daily Excel Report', readonly = True)
	file_name = fields.Char('Excel File', size=64,readonly=True)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
