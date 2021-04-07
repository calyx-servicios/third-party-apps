###############################################################################
#                                                                             #
#    Globalteckz                                                              #
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)        #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU Affero General Public License as           #
#    published by the Free Software Foundation, either version 3 of the       #
#    License, or (at your option) any later version.                          #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU Affero General Public License for more details.                      #
#                                                                             #
#    You should have received a copy of the GNU Affero General Public License #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
###############################################################################


from odoo import fields,models, api

import requests
import json

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    gt_shopify_order = fields.Boolean(string='Shopify Order',readonly=True)
    gt_shopify_order_id = fields.Char(string='Order ID',readonly=True)
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance',readonly=True)
    gt_shopify_order_confirmed = fields.Boolean(string='Order Confirmed',readonly=True)
    gt_shopify_order_status_url = fields.Char(string='Order Status URL',readonly=True)
    gt_shopify_order_cancel_reason = fields.Text(string='Cancel Reason')
    gt_shopify_order_currency = fields.Char(string='Order Currency', readonly=True)
    gt_shopify_tax_included = fields.Boolean(string='Tax Included', readonly=True)
    gt_shopify_financial_status = fields.Char('Payment Status',readonly=True)
    gt_shopify_fulfillment_status = fields.Char('Delivery Status',readonly=True)
    gt_shopify_order_status = fields.Char('Order Status',readonly=True)
    
    
    
    @api.multi
    def gt_update_shopify_order(self):
        
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        shop_url = shopify_url + 'admin/api/2021-01/orders.json?status=any&ids='+ str(self.gt_shopify_order_id)
        response = requests.get( shop_url,auth=(api_key,api_pass))
        order = json.loads(response.text)

        self.write({'gt_shopify_financial_status': order['orders'][0]['financial_status']})                        
        self.write({'gt_shopify_fulfillment_status': 'Not ready'if order['orders'][0]['fulfillment_status'] == None else order['orders'][0]['fulfillment_status']})
        self.write({'gt_shopify_order_status': self.gt_shopify_instance_id._get_shopify_status(self.gt_shopify_order_id)})
        
        if self.state in ['draft','sent'] and self.gt_shopify_financial_status == 'paid':
            self.action_confirm()