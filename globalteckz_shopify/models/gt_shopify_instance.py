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


from odoo import fields,api,models
import requests
import json
import datetime
import base64
import urllib
from datetime import date, datetime
import logging
from logging import getLogger
logger = logging.getLogger('product')
_logger = getLogger(__name__)

class GTShopifyInstance(models.Model):
    _name='gt.shopify.instance'
    _rec_name = 'gt_name'
    
    gt_name = fields.Char(string='Instance Name',size=64, required=True)
    gt_location = fields.Char(string='Location',size=64,required=True)
    gt_api_key = fields.Char(string='Api Key',size=64,required=True)
    gt_password = fields.Char(string='password',size=64,required=True)
    gt_workflow_id = fields.Many2one('gt.import.order.workflow', string='Workflow & Settings')
    count_shopify_shop = fields.Integer(compute='get_shopify_shop_count')
    count_shopify_orders = fields.Integer(compute='get_shopify_orders_count')
    count_shopify_customers = fields.Integer(compute='get_shopify_customers_count')
    count_shopify_template = fields.Integer(compute='get_shopify_template_count')
    count_shopify_variant = fields.Integer(compute='get_shopify_variant_count')
    
    
    @api.multi
    def get_shopify_template_count(self):
        templ_obj = self.env['product.template']
        res = {}
        for shop in self:
            multishop_ids = templ_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_template = len(multishop_ids.ids)
        return res
    
    
    @api.multi
    def get_shopify_variant_count(self):
        prod_obj = self.env['product.product']
        res = {}
        for shop in self:
            multishop_ids = prod_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_variant   = len(multishop_ids.ids)
        return res
    
    
    @api.multi
    def get_shopify_shop_count(self):
        shop_obj = self.env['gt.shopify.store']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_shop = len(multishop_ids.ids)
        return res
    
    @api.multi
    def get_shopify_orders_count(self):
        order_obj = self.env['sale.order']
        res = {}
        for shop in self:
            multishop_ids = order_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_orders = len(multishop_ids.ids)
        return res
    
    
    @api.multi
    def get_shopify_customers_count(self):
        order_obj = self.env['res.partner']
        res = {}
        for shop in self:
            multishop_ids = order_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_customers = len(multishop_ids.ids)
        return res

    @api.one
    def gt_create_shopify_store(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Create Shopify Store','description': 'Successfull','gt_shopify_instance_id': self.id})
        store_obj = self.env['gt.shopify.store']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/shop.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            store_dic=json.loads(response.text)
            stores = store_dic['shop']
            vals = {
                'gt_store_name':stores['name'] if 'name' in stores else '',
                'gt_store_province':stores['province'] if 'province' in stores else '',
                'gt_store_province_code':stores['province_code'] if 'province_code' in stores else '',
                'gt_store_address1':stores['address1'] if 'address1' in stores else '',
                'gt_store_address2':stores['address2'] if 'address2' in stores else '',
                'gt_store_domain':stores['domain'] if 'domain' in stores else '',
                'gt_store_country_code':stores['country_code'] if 'country_code' in stores else '',
                'gt_store_zipcode':stores['zip'] if 'zip' in stores else '',
                'gt_store_city':stores['city'] if 'city' in stores else '',
                'gt_store_id':stores['id'] if 'id' in stores else '',
                'gt_store_currency':stores['currency'] if 'currency' in stores else '',
                'gt_store_email':stores['email'] if 'email' in stores else '',
                'gt_store_weight_unit':stores['weight_unit'] if 'weight_unit' in stores else '',
                'gt_store_country_name':stores['country_name'] if 'country_name' in stores else '',
                'gt_store_shop_owner':stores['shop_owner'] if 'shop_owner' in stores else '',
                'gt_store_plan_display_name':stores['plan_display_name'] if 'plan_display_name' in stores else '',
                'gt_store_phone':stores['phone'] if 'phone' in stores else '',
                'gt_shopify_instance_id': self.id,
                'primary_stock_location': stores['primary_location_id'] if 'primary_location_id' in stores else '',
            }
            stores_id = store_obj.search([('gt_store_id','=',stores['id'])])
            if len(stores_id) > 0:
                stores_id.write(vals)
            else:
                store_obj.create(vals)
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_line_obj.create({'name':'Create Shopify Store','description':exc,'create_date':date.today(),
                                      'shopify_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 

        return True
    
    @api.one
    def gt_import_shopify_product_template(self,shopify_product_id):   
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/api/2022-01/products/'+str(shopify_product_id)+'.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            product_rs=json.loads(response.text)
            product_item = product_rs['product']
            product_tmpl_obj.gt_create_product_template(product_item,self,log_id)
        
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 

        return True

    @api.one
    def gt_import_shopify_products(self):    
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/products.json?limit=250'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            product_rs=json.loads(response.text)
            product_items = product_rs['products']
            
            for products in product_items:
                product_tmpl_obj.gt_create_product_template(products,self,log_id)
        
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
       
        return True
    
    
    @api.multi
    def cron_execute(self):
        _logger.info("INIT %s: CRON SHOPIFY" % (datetime.now().strftime('%m/%d/%Y, %H:%M:%S')))
        shopify_instances = self.env['gt.shopify.instance'].search([])
        for rec in shopify_instances:
            rec.gt_import_shopify_customers()
            rec.gt_import_shopify_products()
            rec.gt_import_shopify_orders()
            rec.gt_export_shopify_stock()
        _logger.info("FINISH %s: CRON SHOPIFY" % (datetime.now().strftime('%m/%d/%Y, %H:%M:%S')))
    
    @api.multi
    def gt_export_shopify_stock(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']

        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', True),('gt_shopify_product','=',True),('gt_shopify_exported','=', True)])
        
        if product_ids:
            for products in product_ids:
                products.update_product_stock()

        return True


    @api.multi
    def _get_instance_primary_stock_location(self):
        stores = self.env['gt.shopify.store'].search([])
        for store in stores:
            if store.gt_shopify_instance_id.id == self.id:
                return store.primary_stock_location

    
    def get_inventory_variant(self, inventory_item_id):

        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        shop_url = shopify_url + 'admin/api/2021-01/inventory_levels.json?inventory_item_ids=' + str(inventory_item_id)
        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_rs=json.loads(response.text)

        for location in product_rs['inventory_levels']:
            if str(location['location_id']) == self._get_instance_primary_stock_location():
                return location['available']

    
    @api.one
    def gt_import_shopify_stock(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Inventory','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_obj = self.env['product.product']
        stock_inve_line_obj=self.env['stock.inventory.line']
        stock_inv_obj=self.env['stock.inventory']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/products.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            product_rs=json.loads(response.text)
            product_items = product_rs['products']
            inventory_id = stock_inv_obj.create({'name':'update stock'+' '+str(datetime.datetime.now())})
            stock_location_id = self.gt_workflow_id.stock_location_id.id

            for products in product_items:
                try:
                    if 'variants' in products:
                        for variant in products['variants']:
                            if 'id' in variant:
                                if 'inventory_quantity' in variant:
                                    if int(variant['inventory_quantity']) > 0:
                                        product_id = product_obj.search([('gt_product_id','=',variant['id'])])
                                        if product_id:
                                            stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':self.gt_workflow_id.stock_location_id.id,'product_id':product_id.id,'product_qty':int(self.get_inventory_variant(variant['inventory_item_id']))})
                                        else:
                                            product_id = product_obj.search([('default_code','=',variant['product_id'])])
                                            if variant['option3'] != None :
                                                for product in product_id:
                                                    variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name, product.attribute_value_ids[2].name ]
                                                    if (variant['option1'] in variantes) and (variant['option2'] in variantes) and (variant['option3'] in variantes):
                                                        stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':self.gt_workflow_id.stock_location_id.id,'product_id':product_id.id,'product_qty':int(self.get_inventory_variant(variant['inventory_item_id']))})

                                            elif variant['option2'] != None:
                                                for product in product_id:
                                                    variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name]
                                                    if (variant['option1'] in variantes) and (variant['option2'] in variantes):
                                                        stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':self.gt_workflow_id.stock_location_id.id,'product_id':product_id.id,'product_qty':int(self.get_inventory_variant(variant['inventory_item_id']))})

                                            elif variant['option1'] != None:
                                                product_id = product_obj.search([('default_code','=',variant['product_id'])])
                                                for product in product_id:
                                                    if product.attribute_value_ids.name == variant['option1'] :
                                                        stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':self.gt_workflow_id.stock_location_id.id,'product_id':product_id.id,'product_qty':int(self.get_inventory_variant(variant['inventory_item_id']))})
                
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    log_line_obj.create({'name':'Create Inventory','description':exc,'create_date':date.today(),
                                              'shopify_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
            inventory_id.action_done()
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True
        
    @api.one
    def gt_import_shopify_image(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']

        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            product_ids = product_tmpl_obj.search([('gt_shopify_product','=',True),('gt_shopify_instance_id','=',self.id),('gt_product_id','!=', False)])
            for products in product_ids:
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id)+'/images.json'
                response = requests.get( shop_url,auth=(api_key,api_pass))
                product_rs=json.loads(response.text)
                product_items = product_rs['images']
                for image in product_items:
                    try:
                        if len(image['variant_ids']) == 0:
                            file_data = urllib.request.urlopen(image['src']).read()
                            image_path = base64.encodestring(file_data)
                            vals = {
                                'gt_image_src': image['src'],
                                'gt_image_id' : image['id'],
                                'gt_is_exported' : True,
                                'gt_image': image_path,
                                'gt_image_position' : image['position'],
                                'gt_product_temp_id': products.id,
                                }
                            photo_id = photo_obj.search([('gt_image_id','=',image['id']),('gt_product_temp_id','=',products.id)])
                            if photo_id:
                                photo_id.write(vals)
                            else:
                                photo_obj.create(vals)
                            image_id_medium = products.write({'image_medium':image_path})
                            image_id_small = products.write({'image_small':image_path})
                        else:
                            for product_ids in image['variant_ids']:
                                product_id = product_obj.search([('gt_product_id','=',product_ids)])
                                if product_id:
                                    file_data = urllib.request.urlopen(image['src']).read()
                                    image_path = base64.encodestring(file_data)
                                    vals = {
                                        'gt_image_src': image['src'],
                                        'gt_image_id' : image['id'],
                                        'gt_is_exported' : True,
                                        'gt_image': image_path,
                                        'gt_image_position' : image['position'],
                                        'gt_product_id': product_id.id,
                                        }
                                    photo_id = photo_obj.search([('gt_image_id','=',image['id']),('gt_product_id','=',product_id.id)])
                                    if photo_id:
                                        photo_id.write(vals)
                                    else:
                                        photo_obj.create(vals)
                                variant_id = product_id.write({'image_medium':image_path})
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        log_line_obj.create({'name':'Create Image','description':exc,'create_date':date.today(),
                                                  'shopify_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True
    
    @api.one
    def gt_import_shopify_customers(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Customers','description': 'Successfull','gt_shopify_instance_id': self.id})
        res_obj = self.env['res.partner']
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
        
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/api/2022-01/customers.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['customers']
            status_id = []
            state_id = False
            country_id = False
            address1 = ''
            address2 = ''
            city = ''
            zip_code = ''
            name = ''
            print('==> shop_url: ',shop_url)
            total_customer_url = shopify_url + 'admin/api/2022-01/customers/count.json'
            total_customer_response = requests.get(total_customer_url,auth=(api_key,api_pass))
            total_customer = json.loads(total_customer_response.text)['count']
            total_count = 0
            print('==> shop_url CUSTOMERS: ',shop_url)

            if 'next' in response.links:
                shop_url_next = response.links['next']['url']
            else:
                shop_url_next = False

            while total_count <= total_customer:
                total_count += len(items)
                print('==> total_count: ',total_count)
                print('==> total_customer: ',total_customer)
                for customer in items:
                    res_partner = res_obj.search([('gt_customer_id','=', customer['id'])])
                    if not res_partner:
                        try:
                            if 'first_name' in customer:
                                name = str(customer['first_name'])
                            if 'last_name' in customer:
                                name = str(customer['first_name']) + ' ' +str(customer['last_name'])
                            if 'state' in customer:
                                status = shopify_state_obj.search([('name','=',str(customer['state']))])
                                if status:
                                    status_id = status.id
                                else:
                                    status_id = shopify_state_obj.create({'name': str(customer['state'])}).id
                                    self.env.cr.commit()
                            if 'default_address' in customer:
                                address = customer['default_address']
                                if 'address1' in address:
                                    address1 = address['address1'] 
                                if 'address2' in address:
                                    address2 = address['address2']
                                if 'city' in address:
                                    city = address['city']
                                if 'zip' in address:
                                    zip_code = address['zip']
                                if 'country' in address and (str(address['country_name']) != 'None'):
                                    if address['country_name'] != None:
                                        country = res_country_obj.search([('name','ilike',str(address['country_name'])), ('code', '=', str(address['country_code']))])
                                        if country:
                                            country_id = country.id
                                        else:
                                            country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id
                                            self.env.cr.commit()
                                        if 'province' in address and (str(address['province']) != 'None'):
                                            state = res_state_obj.search([('name','ilike',str(address['province'])), ('country_id', '=', country_id), ('code', '=', str(address['province_code']))])
                                            if state:
                                                state_id = state.id
                                            else:
                                                value_state = {
                                                    'name': str(address['province']),
                                                    'country_id': country_id, 
                                                    'code':str(address['province_code']) if 'province_code' in address else ''}
                                                state_id = res_state_obj.create(value_state).id
                                                self.env.cr.commit()
                            vals = {
                                'gt_customer_note': customer['note']if 'note' in customer else '',
                                'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
                                'gt_customer_id': customer['id'] if 'id' in customer else '',
                                'gt_shopify_customer': True,
                                'email': customer['email'] if 'email' in customer else '',
                                'phone': customer['phone'] if 'phone' in customer else '',
                                'gt_customer_state' : status_id,
                                'country_id': country_id,
                                'state_id': state_id,
                                'street': address1,
                                'street2':address2,
                                'city': city,
                                'zip': zip_code,
                                'name': name,
                                'gt_default_country_id': country_id,
                                'gt_default_state_id': state_id,
                                'gt_default_street': address1,
                                'gt_default_street2':address2,
                                'gt_default_city': city,
                                'gt_default_zip': zip_code,
                                'gt_default_name': name+'_s',
                                'gt_shopify_instance_id' : self.id
                            }
                            res = res_obj.create(vals)
                            self.env.cr.commit()

                        except Exception as exc:
                            logger.error('Exception===================:  %s', exc)
                            log_line_obj.create({'name':'Create Customer','description':exc,'create_date':date.today(),
                                                    'shopify_log_id':log_id.id})
                            log_id.write({'description': 'Something went wrong'})
                            self.env.cr.commit()

                if shop_url_next:
                    response = requests.get( shop_url_next,auth=(api_key,api_pass))
                    customer_rs = json.loads(response.text)
                    items = customer_rs['customers']
                    print('===> url: ',shop_url_next)
                    print('===> Faltan: ',len(items))
                    if 'next' in response.links:
                        shop_url_next = response.links['next']['url']

        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            
        return True
    
    
    def _get_shopify_status(self, order_id):
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        shop_url = shopify_url + 'admin/api/2021-01/orders.json?status=closed&ids='+str(order_id)        
        response = requests.get(shop_url,auth=(api_key,api_pass))
        response_order_status=json.loads(response.text)
        if len(response_order_status['orders'])>0:
            return 'Closed'
        else:
            shop_url = shopify_url + 'admin/api/2021-01/orders.json?status=open&ids='+str(order_id)        
            response = requests.get(shop_url,auth=(api_key,api_pass))
            response_order_status=json.loads(response.text)
            if len(response_order_status['orders'])>0:
                return 'Open'
            else:
                shop_url = shopify_url + 'admin/api/2021-01/orders.json?status=cancelled&ids='+str(order_id)        
                response = requests.get(shop_url,auth=(api_key,api_pass))
                response_order_status=json.loads(response.text)
                if len(response_order_status['orders'])>0:
                    return 'Cancelled'            

    @api.one
    def gt_import_shopify_orders(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Orders','description': 'Successfull','gt_shopify_instance_id': self.id})
        res_obj = self.env['res.partner']
        sale_obj = self.env['sale.order']
        prod_obj = self.env['product.product']
        tax_obj = self.env['account.tax']
        payment_obj = self.env['account.payment.term']
        product_templ_obj = self.env['product.template']
        product_lines = []
        product_untracked_lines = []

        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/orders.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['orders']
            print('==> shop_url: ',shop_url)
            print('==> COUNT. ITEMS: ', len(items))
            total_order_url = shopify_url + 'admin/api/2022-01/orders/count.json'
            total_order_response = requests.get( total_order_url,auth=(api_key,api_pass))
            total_order = json.loads(total_order_response.text)['count']
            total_count = 0
            
            logger.info('Total Orders===================:  %s', total_order)

            if 'next' in response.links:
                shop_url_next = response.links['next']['url']
            else:
                shop_url_next = False
        
            while total_count <= total_order:
                
                total_count += len(items)

                logger.info('Total Request ===================:  %s', total_count)

                print("==> total_count: ",total_count)
                print("==> total_order: ",total_order)
                for order in items:
                    payment_id = []
                    order_confirm = []
                    order_stauts_url = ''
                    order_currency = ''
                    tax_incl = ''
                    try:
                        if 'confirmed' in order:
                            order_confirm = order['confirmed']
                        if 'currency' in order:
                            order_currency = order['currency']
                        if 'order_status_url' in order:
                            order_stauts_url = order['order_status_url']
                        if 'taxes_included' in order:
                            tax_incl = order['taxes_included']
                        if 'customer' in order:
                            customer = order['customer']
                            cust_id = res_obj.search([('gt_customer_id','=', customer['id'])])
                            if cust_id:
                                customer_id = cust_id
                            else:
                                customer_id =  self.create_order_customer(res_obj,customer)
                                self.env.cr.commit()
                            if customer_id:
                                if 'shipping_address' in order:
                                    shipping_address = order['shipping_address']
                                    self.update_shipping_address(shipping_address,customer_id)
                                    self.env.cr.commit()

                            if 'line_items' in order:
                                items = order['line_items']
                                product_lines = []
                                product_untracked_lines = []
                                product_id = False

                                for lines in items:
                                    if lines['variant_id'] != None:
                                        product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                        if product:
                                            product_id = product
                                        else: 
                                            self.gt_import_shopify_product_template(lines['product_id'])
                                            self.env.cr.commit()
                                            product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                            if product:
                                                product_id = product

                                        if 'tax_lines' in lines:
                                            ta_line = lines['tax_lines']
                                            tax_list = []
                                            for tax_line in ta_line: 
                                                tax = tax_obj.search([('name','=',str(tax_line['title'])),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                                if tax:
                                                    tax_id = tax
                                                else:
                                                    print("===> POR CREAR TAX: ",tax_line['title'])
                                                    tax_id = tax_obj.create({'name':tax_line['title'],'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                                    self.env.cr.commit()
                                                tax_list.append(tax_id.id)
                                        
                                        if product_id:
                                            if product_id.gt_product_inventory_tracked:
                                                product_lines.append((0,0,{
                                                    'product_id': product_id.id or False,
                                                    'name': product_id.name or 'Producto Sin Nombre',###,###
                                                    'template_id': product_id.product_tmpl_id.id or False,
                                                    'variants_status_ok':True,'tax_id': [(6, 0,tax_list)] or False,
                                                    'price_unit':lines['price'],
                                                    'product_uom_qty': lines['quantity'],
                                                }))

                                            else:
                                                product_untracked_lines.append((0,0,{
                                                    'product_id': product_id.id,
                                                    'name': product_id.name or 'Producto Sin Nombre',###
                                                    'template_id': product_id.product_tmpl_id.id,###
                                                    'variants_status_ok':True,'tax_id': [(6, 0,tax_list)],###
                                                    'price_unit':lines['price'],
                                                    'product_uom_qty': lines['quantity'],
                                                }))
                                        else:
                                            logger.info('No Existe El Producto ===================:  %s', lines['product_id'])

                        # Como la SO puede contener productos con seguimiento de inventario, o no.
                        # Se crearan 2 ordenes de venta para utilizar almacenes diferentes.
                        # Ya que los que deban ir a fabricacion, deberian estar asociados a un almacen que tenga configurada esa ruta.
                        sale_ids = sale_obj.search([('name','=',str(order['order_number'])),('gt_shopify_order_id','=',str(order['id']))])

                        if not sale_ids:
                            if product_lines:                      
                                value = {
                                    'name':str(order['order_number']),
                                    'partner_id':customer_id.id, 
                                    'order_line': product_lines,
                                    'warehouse_id': self.gt_workflow_id.warehouse_id.id,
                                    'gt_shopify_instance_id': self.id, 
                                    'gt_shopify_order': True,
                                    'payment_term_id':payment_id,
                                    'gt_shopify_order_id': order['id'],
                                    'gt_shopify_order_status_url':order_stauts_url,
                                    'gt_shopify_order_confirmed':order_confirm,
                                    'gt_shopify_order_currency':order_currency,
                                    'gt_shopify_tax_included':tax_incl,
                                    'gt_shopify_financial_status':order['financial_status'],
                                    'gt_shopify_fulfillment_status': 'Not ready'if order['fulfillment_status'] == None else order['fulfillment_status'],
                                    'gt_shopify_order_status': self._get_shopify_status(order['id']),
                                    'gt_shopify_payment_gateway_names': str(order['payment_gateway_names'][0]) if order['payment_gateway_names'] else '',
                                    'email_partner': customer_id.email if customer_id.email  else 'No Suministrado',
                                }
                                print("===> CREATE SO: ",str(order['order_number']))
                                sale_order = sale_obj.create(value)
                                self.env.cr.commit()
                                logger.info('Create Order===================:  %s', sale_order.name)
                                
                            if product_untracked_lines:
                                vals = {
                                    'name':str(order['order_number']),
                                    'partner_id':customer_id.id, 
                                    'order_line': product_untracked_lines,
                                    'warehouse_id': self.gt_workflow_id.warehouse_manufacturing_id.id,
                                    'gt_shopify_instance_id': self.id, 
                                    'gt_shopify_order': True,
                                    'payment_term_id':payment_id,
                                    'gt_shopify_order_id': order['id'],
                                    'gt_shopify_order_status_url':order_stauts_url,
                                    'gt_shopify_order_confirmed':order_confirm,
                                    'gt_shopify_order_currency':order_currency,
                                    'gt_shopify_tax_included':tax_incl,
                                    'gt_shopify_financial_status':order['financial_status'],
                                    'gt_shopify_fulfillment_status': 'Not ready'if order['fulfillment_status'] == None else order['fulfillment_status'],
                                    'gt_shopify_order_status': self._get_shopify_status(order['id']),
                                    'gt_shopify_payment_gateway_names': str(order['payment_gateway_names'][0]) if order['payment_gateway_names'] else '',
                                    'email_partner': customer_id.email if customer_id.email  else 'No Suministrado',
                                }
                                print("===> CREATE SO, sale_order_manufacturing => ",str(order['order_number']))
                                sale_order_manufacturing = sale_obj.create(vals)
                                self.env.cr.commit()
                                logger.info('Create Order===================:  %s', sale_order_manufacturing.name)

                        else:
                            for sale_id in sale_ids:       
                                vals_update = {
                                    'gt_shopify_payment_gateway_names': str(order['payment_gateway_names'][0]) if order['payment_gateway_names'] else '',
                                    'gt_shopify_financial_status': order['financial_status'],
                                    'gt_shopify_fulfillment_status': 'Not ready'if order['fulfillment_status'] == None else order['fulfillment_status'],
                                    'gt_shopify_order_status': self._get_shopify_status(order['id'])
                                }
                                print("===> WRITE SO => ",str(order['order_number']))
                                sale_id.write(vals_update)
                                self.env.cr.commit()
                                logger.info('Update Order===================:  %s', sale_id.name)

                                if sale_id.state in ['draft','sent'] and sale_id.gt_shopify_financial_status == 'paid':
                                    sale_id.action_confirm()
                                    self.env.cr.commit()
                            
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        log_line_obj.create({'name':'Create Order',
                        'description':exc,
                        'create_date':date.today(),
                        'shopify_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 

                if shop_url_next:
                    response = requests.get( shop_url_next,auth=(api_key,api_pass))
                    customer_rs = json.loads(response.text)
                    items = customer_rs['orders']
                    
                    print('===> url: ',shop_url_next)
                    print('===> Faltan: ',len(items))
                    if 'next' in response.links:
                        shop_url_next = response.links['next']['url']
                    else:
                        shop_url_next = False

                    
                    logger.info('Orders Count Response ===================:  %s', len(items))
                    total_count
                
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True
        
    
    @api.multi
    def update_shipping_address(self,address,customer_id):
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
        country_id = state_id = False
        address1 = address2 = city = zip_code = False

        if 'address1' in address:
            address1 = address['address1'] 
            if 'address2' in address:
                address2 = address['address2']
            if 'city' in address:
                city = address['city']

            if 'zip' in address:
                zip_code = str(address['zip']) or '' ###
            if 'country' in address and (str(address['country']) != 'None'):
                country = res_country_obj.search([('name','ilike',str(address['country']))])
                if country:
                    country_id = country.id
                else:
                    country_value = {
                        'name': str(address['country']),
                        'code': str(address['country_code']) if 'country_code' in address else ''
                    }
                    country_id = res_country_obj.create(country_value).id
                    self.env.cr.commit()
            if 'province' in address and (str(address['province']) != 'None'):
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:
                    state_id = state.id
                else:
                    state_value = {
                        'name': str(address['province']),
                        'country_id': country_id, 
                        'code':str(address['province_code']) if 'province_code' in address else ''
                    }
                    state_id = res_state_obj.create(state_value).id
                    self.env.cr.commit()
        if country_id and state_id:
            value_customer = {
                'country_id': country_id,
                'state_id': state_id,
                'street': address1,
                'street2':address2,
                'city': city,
                'zip': zip_code,
            }
            print("===> WRITE CUSTOMER => ",customer_id.name)
            customer_id.write(value_customer)
            self.env.cr.commit()
        
        return True
        

    @api.multi
    def create_order_customer(self,res_obj,customer): 
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
        country_id = state_id = False
        address1 = address2 = city = zip_code = False
        if  'first_name' in customer:  
            name = str(customer['first_name'])  
            if 'last_name' in customer:
                name = str(customer['first_name']) + ' ' +str(customer['last_name'])
                                      
            if 'state' in customer:
                status = shopify_state_obj.search([('name','=',str(customer['state']))])
                if status:
                    status_id = status.id
                else:
                    status_id = shopify_state_obj.create({'name': str(customer['state'])}).id

        if 'default_address' in customer:
            address = customer['default_address']
            if 'address1' in address:
               address1 = address['address1'] 
            if 'address2' in address:
                address2 = address['address2']
            if 'city' in address:
                city = address['city']
            if 'zip' in address:
                zip_code = address['zip']
            if 'country' in address and (str(address['country_name']) != 'None'):
                country = res_country_obj.search([('name','=',str(address['country_name']))])
                if country:##SI EXISTE EL PAIS EN ODOO, USAMOS ESE
                    country_id = country.id
                else:
                    country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id

            if 'province' in address and (str(address['province']) != 'None'):
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:##SI EXISTE LA PROVINCIA EN ODOO, USAMOS ESE
                    state_id = state.id
                else:
                    state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id

        customer_id = res_obj.create({
            'name': name,
            'gt_customer_note': customer['note']if 'note' in customer else '',
            'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
            'gt_customer_id': customer['id'] if 'id' in customer else '',
            'gt_shopify_customer': True,
            'email': customer['email'] if 'email' in customer else '',
            'phone': customer['phone'] if 'phone' in customer else '',
            'gt_customer_state' : status_id,
            'gt_default_country_id': country_id,
            'gt_default_state_id': state_id,
            'gt_default_street': address1,
            'gt_default_street2':address2,
            'gt_default_city': city,
            'gt_default_zip': zip_code,
            'gt_default_name': name,
            'gt_shopify_instance_id': self.id
        })

        ### SI EL EMAIL SE ENCUENTRA EN ODOO. LO ACTUALIZAMOS
        # validation_name_in_odoo = res_obj.search([('email','=',customer['email'])])
        # if validation_name_in_odoo:
        #     value = {
        #         'email': customer['email'] if 'email' in customer else '',
        #         'phone': customer['phone'] if 'phone' in customer else '',
        #         'gt_customer_note': customer['note']if 'note' in customer else '',
        #         'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
        #         'gt_customer_id': customer['id'] if 'id' in customer else '',
        #         'gt_shopify_customer': True,
        #         'gt_customer_state' : status_id,
        #         'gt_default_country_id': country_id,
        #         'gt_default_state_id': state_id,
        #         'gt_default_street': address1,
        #         'gt_default_street2':address2,
        #         'gt_default_city': city,
        #         'gt_default_zip': zip_code,
        #         'gt_default_name': name,
        #         'gt_shopify_instance_id': self.id
        #     }
        #     customer_id = res_obj.write(value)
        # ### SI EL EMAIL NO EXISTE EN ODOO, CREAMOS UN CONTACTO NUEVO
        # else:
        #     value = {
        #         'name': name,
        #         'email': customer['email'] if 'email' in customer else '',
        #         'phone': customer['phone'] if 'phone' in customer else '',
        #         'gt_customer_note': customer['note']if 'note' in customer else '',
        #         'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
        #         'gt_customer_id': customer['id'] if 'id' in customer else '',
        #         'gt_shopify_customer': True,               
        #         'gt_customer_state' : status_id,
        #         'gt_default_country_id': country_id,
        #         'gt_default_state_id': state_id,
        #         'gt_default_street': address1,
        #         'gt_default_street2':address2,
        #         'gt_default_city': city,
        #         'gt_default_zip': zip_code,
        #         'gt_default_name': name,
        #         'gt_default_phone': customer['phone'] if 'phone' in customer else '',
        #         'gt_shopify_instance_id': self.id
        #     }
        #     customer_id = res_obj.create(value)
  
        return customer_id
    
    
    
    @api.multi
    def action_get_shop(self):
        shopify_shop = self.env['gt.shopify.store'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.action_gt_shopify_store')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_shop.ids)]
        }

        return result
    
    
    @api.multi
    def action_get_orders(self):
        shopify_orders = self.env['sale.order'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.action_orders_shopify_all')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_orders.ids)]
        }

        return result
    
    
    @api.multi
    def action_get_customers(self):
        shopify_customers = self.env['res.partner'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.action_customers_shopify_all')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_customers.ids)]
        }

        return result
    
    
    
    @api.multi
    def action_get_product_template(self):
        shopify_templ = self.env['product.template'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.shopify_product_template_exported')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_templ.ids)]
        }

        return result
    
    
    
    @api.multi
    def action_get_product_variant(self):
        shopify_prod = self.env['product.product'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.shopify_products_variant_exported')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_prod.ids)]
        }

        return result