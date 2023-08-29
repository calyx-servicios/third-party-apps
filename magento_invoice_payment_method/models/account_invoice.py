# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    magento_payment_method = fields.Char(compute="_compute_magento_payment_method", string="Magento Payment Method")


    def _compute_magento_payment_method(self):
        magento_payment_method_name = ''

        sale_orders = self.env['sale.order']._search_invoice_ids('in',{self.id})
        if sale_orders:
            sale_order = self.env['sale.order'].search([('id','=',sale_orders[0][2][0])])
            if sale_order:
                magento_payment_method_name = sale_order[0].payment_method.name

        self.magento_payment_method = magento_payment_method_name


