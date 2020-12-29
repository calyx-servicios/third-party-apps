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

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    gt_shopify_order = fields.Boolean(string='Shopify Order',readonly=True)
    gt_shopify_shipped = fields.Boolean(string='Shipped',readonly=True)
    gt_shopify_order_id = fields.Char(string='Order ID',readonly=True)
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance',readonly=True)
    gt_shopify_order_confirmed = fields.Boolean(string='Order Confirmed',readonly=True)
    gt_shopify_order_status_url = fields.Char(string='Order Status URL',readonly=True)
    gt_shopify_order_cancel_reason = fields.Text(string='Cancel Reason')
    gt_shopify_order_currency = fields.Char(string='Order Currency', readonly=True)
    gt_shopify_tax_included = fields.Boolean(string='Tax Included', readonly=True)
    gt_shopify_close_order = fields.Boolean(string='Order Closed')
    
    
    
    
    @api.multi
    def gt_close_shopify_order(self):
        print( True)
        
        
    @api.multi
    def gt_reopen_shopify_order(self):
        print (True)
    
    