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


from odoo import fields, api, models
from odoo.exceptions import ValidationError
import requests, json


class ProductProduct(models.Model):
    _inherit='product.product'
    
    gt_requires_shipping = fields.Boolean(string='Requires Shipping')
    gt_product_id = fields.Char(string='Product ID')
    gt_title = fields.Char(string='Title')
    gt_inventory_policy = fields.Many2one('gt.inventory.policy', string='Inventory Policy')
    gt_fulfillment_service = fields.Char(string='Fulfillment Service')
    gt_shopify_product = fields.Boolean(string='Shopify Product')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_product_image_id = fields.One2many('gt.product.photo', 'gt_product_id', string='Product Images')
    gt_shopify_exported = fields.Boolean(string='Shopify Exported')
    gt_fullfilment_service = fields.Many2one('gt.fulfillment.service', string='Fullfilment Service')
    gt_inventory_management = fields.Many2one('gt.inventory.management', string='Inventory Management')
    gt_product_inventory_id = fields.Char('Product Inventory ID')
    gt_product_price_compare = fields.Float('Product Price Compare')
    gt_product_inventory_tracked = fields.Boolean('Tracking')
    

    @api.constrains('gt_product_price_compare')
    def _check_gt_product_price_compare(self):
        if self.lst_price >= self.gt_product_price_compare:
            raise ValidationError('The "Product Price Compare" must be greater than the list price.')

    @api.multi
    def _get_primary_stock_location(self):
        stores = self.env['gt.shopify.store'].search([])
        for store in stores:
            if store.gt_shopify_instance_id.id == self.product_tmpl_id.gt_shopify_instance_id.id:
                return store.primary_stock_location

    @api.multi
    def update_variant(self,products_response,instance,log_id):
        policy_obj = self.env['gt.inventory.policy']
        uom_obj = self.env['product.uom']
        log_line_obj = self.env['shopify.log.details']
        management_obj = self.env['gt.inventory.management']
        fullfilment_obj = self.env['gt.fulfillment.service']
        policies = []
        weights = []
        management = []
        fullfilment = []
        try:
            if 'inventory_management' in products_response:
                management_id = management_obj.search([('name','=',products_response['inventory_management']),('gt_shopify_instance_id','=',instance.id)])
                if len(management_id) > 0 :
                    management = management_id.id
                else:
                    management = management_obj.create({'name':str(products_response['inventory_management']),'gt_shopify_instance_id':instance.id}).id
            if 'fulfillment_service' in products_response:
                fullfilment_id = fullfilment_obj.search([('name','=',products_response['fulfillment_service']),('gt_shopify_instance_id','=',instance.id)])
                if len(fullfilment_id) > 0 :
                    fullfilment = fullfilment_id.id
                else:
                    fullfilment = fullfilment_obj.create({'name':str(products_response['fulfillment_service']),'gt_shopify_instance_id':instance.id}).id
            if 'inventory_policy'in products_response:
                policy_id = policy_obj.search([('name','=',products_response['inventory_policy']),('gt_shopify_instance_id','=',instance.id)])
                if len(policy_id) > 0 :
                    policies =  policy_id.id
                else:
                    policies = policy_obj.create({'name':str(products_response['inventory_policy']),'gt_shopify_instance_id':instance.id}).id
            if 'weight_unit' in products_response:
                weight_id = uom_obj.search([('name','=',str(products_response['weight_unit']))])
                if len(weight_id) > 0 :
                    weights = weight_id.id
                else:
                    weights = uom_obj.create({'name':str(products_response['weight_unit']),'gt_shopify_instance_id':instance.id}).id
            
            vals = {
                'gt_requires_shipping': str(products_response['requires_shipping']) if 'requires_shipping' in products_response else '',
                'gt_product_id': products_response['id'] if 'id' in products_response else '',
                'weight': products_response['weight'] if 'weight' in products_response else '',
                'default_code' : products_response['sku'] if 'sku' in products_response else '',
                'gt_fulfillment_service' : products_response['fulfillment_service'] if 'fulfillment_service' in products_response else '',
                'gt_inventory_policy': policies,
                'gt_shopify_instance_id': instance.id,
                'gt_shopify_exported': True,
                'gt_shopify_product':True,
                'gt_fullfilment_service': fullfilment,
                'gt_inventory_management':management,
                'gt_product_price_compare': products_response['compare_at_price'],
            }
            self.write(vals)

        except Exception as exc:
            log_line_obj.create({'name':'Create Product Template','description':exc,'status':'ERROR','create_date': fields.date.today(),
                                      'shopify_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 
        return True
    
    @api.multi
    def _is_inventory_tracking(self, shopify_instance_id):
        inventory_tracking = False
        shopify_url = str(shopify_instance_id.gt_location)
        api_key = str(shopify_instance_id.gt_api_key)
        api_pass = str(shopify_instance_id.gt_password)
        shop_url = shopify_url + '/admin/api/2021-01/inventory_items/'+ str(self.gt_product_inventory_id)+ '.json'
        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_rs = json.loads(response.text)
        
        if 'inventory_item' in product_rs:
            if 'tracked' in product_rs['inventory_item']:
                inventory_tracking = product_rs['inventory_item']['tracked']

        return inventory_tracking


class GtInventoryPolicy(models.Model):
    _name = 'gt.inventory.policy'
    
    name = fields.Char(string='Inventory Policy')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
    
class GtInventoryManagement(models.Model):
    _name = 'gt.inventory.management'
    
    name = fields.Char(string='Inventory Management')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
    
class GtFulfillmentService(models.Model):
    _name = 'gt.fulfillment.service'
    
    name = fields.Char(string='Fulfillment Service')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')

