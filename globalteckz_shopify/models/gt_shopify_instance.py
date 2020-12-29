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
from datetime import date
import logging
logger = logging.getLogger('product')

class GTShopifyInstance(models.Model):
    _name='gt.shopify.instance'
    _rec_name = 'gt_name'
    
    gt_name = fields.Char(string='Instance Name',size=64, required=True)
    gt_location = fields.Char(string='Location',size=64,required=True)
    gt_api_key = fields.Char(string='Api Key',size=64,required=True)
    gt_password = fields.Char(string='password',size=64,required=True)
    gt_worflow_id = fields.Many2one('gt.import.order.workflow', string='Workflow & Settings')
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
            shop_url = shopify_url + 'admin/products.json'
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
    def gt_export_shopify_products(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', False),('gt_shopify_product','=',True)])
        ids = product_tmpl_obj.search([('id','=', 7)])
        ids.write({'gt_shopify_exported':True})
        self._cr.commit()
        if product_ids:
            for products in product_ids:
                tag = ''
                if len(products.gt_product_tags) == 1:
                    tag = str(products.gt_product_tags.name)
                else:
                    for tags in products.gt_product_tags:
                        tag += str(tags.name)+',' 
                if len(products.product_variant_ids) == 1:
                    vals = {        
                        "product": {
                            "title":str(products.name),
                            "body_html":str(products.gt_shopify_description),
                            "vendor": str(products.gt_vendor.name),
                            "product_type": str(products.gt_shopify_product_type.name),
                            "published_scope" : str(products.gt_published_scope.name),
                            "tags": tag,
                            "variants": [
                                {
                                  "price": str(products.list_price),
                                  "sku": str(products.default_code),
                                  #"inventory_policy": products.product_variant_ids.gt_inventory_policy.name,
                                  "fulfillment_service": str(products.product_variant_ids.gt_fullfilment_service.name),
                                  "inventory_management": str(products.product_variant_ids.gt_inventory_management.name),
                                  "taxable": str(True),
                                  "barcode": str(products.barcode),
                                  "weight": str(products.weight),
                                  "weight_unit": str(products.product_variant_ids.uom_id.name),
                                  "requires_shipping": str(products.product_variant_ids.gt_requires_shipping),
                                }
                              ],
                        }
                    }
                else:
                    list_variant = []
                    option1_list = []
                    option2_list = []
                    option3_list = []
                    attribute1 = ''
                    attribute2 = ''
                    attribute3 = ''
                    options = []
                    for atts in products.product_variant_ids[0]:
                        if len(atts.attribute_value_ids) == 1:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                        elif len(atts.attribute_value_ids) == 2:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                            attribute2 = str(atts.attribute_value_ids[1].attribute_id.name)
                        elif len(atts.attribute_value_ids) == 3:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                            attribute2 = str(atts.attribute_value_ids[1].attribute_id.name)
                            attribute3 = str(atts.attribute_value_ids[2].attribute_id.name)
                    for variants in products.product_variant_ids:
                        option1 = ''
                        option2 = ''
                        option3 = ''
                        if len(variants.attribute_value_ids) == 3:
                            for atts in variants.attribute_value_ids:
                                if attribute1 == str(atts.attribute_id.name):
                                    option1 = str(atts.name)
                                    if str(atts.name) not in option1_list:
                                        option1_list.append(option1)
                                elif attribute2 == str(atts.attribute_id.name):
                                    option2 = str(atts.name)
                                    if str(atts.name) not in option2_list:
                                        option2_list.append(option2)
                                elif attribute3 == str(atts.attribute_id.name):
                                    option3 = str(atts.name)
                                    if str(atts.name) not in option3_list:
                                        option3_list.append(option3)
                        vals_variant = {
                                "price": str(variants.lst_price),
                                "sku": str(variants.default_code),
                                #"inventory_policy": products.product_variant_ids.gt_inventory_policy.name,
                                "fulfillment_service": str(variants.gt_fullfilment_service.name),
                                "inventory_management": str(variants.gt_inventory_management.name),
                                "taxable": str(True),
                                "barcode": str(variants.barcode),
                                "weight": str(variants.weight),
                                "weight_unit": str(variants.uom_id.name),
                                "requires_shipping": str(variants.gt_requires_shipping),
                                "option1": option1,
                                "option2": option2,
                                "option3": option3,
                              }
                        list_variant.append(vals_variant)
                    if len(option1_list) > 0:
                        vals_option = {"name": attribute1,"position": 1,"values": option1_list}
                        options.append(vals_option)
                    if len(option2_list) > 0:
                        vals_option = { "name": attribute2,"position": 2,"values": option2_list}
                        options.append(vals_option)
                    if len(option3_list) > 0:
                        vals_option = {"name": attribute3,"position": 3,"values": option3_list}
                        options.append(vals_option)
                    vals = {
                        "product": {
                          "title": str(products.name),
                          "body_html": str(products.gt_shopify_description),
                          "vendor": str(products.gt_vendor.name),
                          "product_type": str(products.gt_shopify_product_type.name),
                          "published_scope" : str(products.gt_published_scope.name),
                          "tags": tag,
                          "variants": list_variant,
                          "options": options,
                        }
                      }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                shop_url = shopify_url + 'admin/products.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)    
                if str(response) == '<Response [201]>':
                    products.write({'gt_shopify_exported': True})
                    products.product_variant_ids.write({'gt_shopify_exported': True})
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    
    @api.multi
    def gt_export_shopify_stock(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = product_obj.search([('gt_shopify_exported','=', True),('gt_shopify_product','=',True)])
        if product_ids:
            for products in product_ids:
                if products.qty_available > 0:
                    vals =  {
                          "product": {
                            "id": str(products.product_tmpl_id.gt_product_id),
                            "variants": [
                              {
                                "id": str(products.gt_product_id),
                                "inventory_quantity": int(products.qty_available),
                                
                              },
                            ]
                          }
                    }
                    payload=str(vals)
                    payload=payload.replace("'",'"')
                    payload=str(payload)
                    shop_url = shopify_url + 'admin/products/'+str(products.product_tmpl_id.gt_product_id)+'.json'
                    response = requests.put( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                    product_rs=json.loads(response.text)    
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    
    
        
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
            for products in product_items:
                try:
                    if 'variants' in products:
                        for variant in products['variants']:
                            if 'sku' in variant:
                                if 'inventory_quantity' in variant:
                                    if int(variant['inventory_quantity']) > 0:
                                        product_id = product_obj.search([('default_code','=',variant['sku'])])
                                        if product_id:
                                            stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':15,'product_id':product_id.id,'product_qty':int(variant['inventory_quantity'])})
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
                            file_data = urllib.urlopen(image['src']).read()
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
                            image_id = products.write({'image_medium':image_path})
                        else:
                            for product_ids in image['variant_ids']:
                                product_id = product_obj.search([('gt_product_id','=',product_ids)])
                                if product_id:
                                    file_data = urllib.urlopen(image['src']).read()
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
    def gt_export_shopify_image(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',self.id)])
        for products in product_ids:
            if products.gt_product_temp_id:
                decodes = products.gt_image.decode("base64")
                newdecode = decodes.encode("base64")
                vals = {
                    "image": {
                      "position": products.gt_image_position,
                      "attachment": newdecode, 
                      "filename": str(products.gt_image_name),
                    }
                  }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_temp_id.gt_product_id)+'/images.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)
                if str(response) == '<Response [200]>':
                    image =  product_rs['image']
                
            if products.gt_product_id:
                decodes = products.gt_image.decode("base64")
                newdecode = decodes.encode("base64")
                vals = {
                    "image": {
                      "variant_ids": [str(products.gt_product_id.gt_product_id)],
                      "position": products.gt_image_position,
                      "attachment": newdecode, 
                      "filename": str(products.gt_image_name),
                    }
                  }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id.product_tmpl_id.gt_product_id)+'/images.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)
                if str(response) == '<Response [200]>':
                    image =  product_rs['image']
                    products.write({'gt_is_exported': True,'gt_image_id':image['id'],'gt_image_src':image['src'],'gt_image_position':image['position']})
                
#                    except Exception as exc:
#                        logger.error('Exception===================:  %s', exc)
#                        log_line_obj.create({'name':'Create Image','description':exc,'create_date':date.today(),
#                                                  'shopify_log_id':log_id.id})
#                        log_id.write({'description': 'Something went wrong'}) 
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
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
            shop_url = shopify_url + 'admin/customers.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['customers']
            status_id = []
            state_id = []
            country_id = []
            address1 = ''
            address2 = ''
            city = ''
            zip_code = ''
            name = ''
            for customer in items:
                try:
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
                        if 'country' in address:
                            country = res_country_obj.search([('name','=',str(address['country_name']))])
                            if country:
                                country_id = country.id
                            else:
                                country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id

                        if 'province' in address:
                            state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                            if state:
                                state_id = state.id
                            else:
                                state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
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
                        'gt_default_name': name,
                        'gt_shopify_instance_id' : self.id
                    }

                    res_id = res_obj.search([('gt_customer_id','=', customer['id'])])
                    if not res_id:
                        ress = res_obj.create(vals)
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    log_line_obj.create({'name':'Create Customer','description':exc,'create_date':date.today(),
                                              'shopify_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True
    
    
    
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
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/orders.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['orders']
            for order in items:
                payment_id = []
                order_confirm = []
                order_stauts_url = ''
                order_currency = ''
                tax_incl = ''
                try:
                    payment = payment_obj.search([('name','=','Immediate Payment')])
                    if payment:
                        payment_id = payment.id
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
                        if customer_id:
                            if 'shipping_address' in order:
                                shipping_address = order['shipping_address']
                                self.update_shipping_address(shipping_address,customer_id)

                        if 'line_items' in order:
                            items = order['line_items']
                            product_lines = []
                            for lines in items:
                                product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                if product:
                                    product_id = product
                                else:
                                    prod_obj.gt_import_shopify_products()
                                    product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                    product_id = product
                                if 'tax_lines' in lines:
                                    ta_line = lines['tax_lines']
                                    tax_list = []
                                    for tax_line in ta_line: 
                                        tax = tax_obj.search([('name','=',str(tax_line['title'])),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                        if tax:
                                            tax_id = tax
                                        else:
                                            tax_id = tax_obj.create({'name':tax_line['title'],'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                        tax_list.append(tax_id.id)
                                product_lines.append((0,0,{'product_id': product_id.id,'tax_id': [(6, 0,tax_list)],'price_unit':lines['price'],'product_uom_qty': lines['quantity'],}))
                    sale_id = sale_obj.search([('name','=',order['order_number']),('gt_shopify_order_id','=',order['id'])])
                    if not sale_id:
                        sale_obj.create({'name':order['order_number'],
                            'partner_id':customer_id.id, 
                            'order_line': product_lines, 
                            'gt_shopify_instance_id': self.id, 
                            'gt_shopify_order': True,
                            'payment_term_id':payment_id,
                            'gt_shopify_order_id': order['id'],
                            'gt_shopify_order_status_url':order_stauts_url,
                            'gt_shopify_order_confirmed':order_confirm,
                            'gt_shopify_order_currency':order_currency,
                            'gt_shopify_tax_included':tax_incl})
                            
                    self._cr.commit()
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    log_line_obj.create({'name':'Create Order','description':exc,'create_date':date.today(),
                                              'shopify_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True
        
    
    @api.multi
    def update_shipping_address(self,address,customer_id):
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']   
        if 'address1' in address:
            address1 = address['address1'] 
            if 'address2' in address:
                address2 = address['address2']
            if 'city' in address:
                city = address['city']
            if 'zip' in address:
                zip_code = address['zip']
            if 'country' in address:
                country = res_country_obj.search([('name','=',str(address['country']))])
                if country:
                    country_id = country.id
                else:
                    country_id = res_country_obj.create({'name': str(address['country']),'code': str(address['country_code']) if 'country_code' in address else ''}).id

            if 'province' in address:
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:
                    state_id = state.id
                else:
                    state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
        customer_id.write({
            'country_id': country_id,
            'state_id': state_id,
            'street': address1,
            'street2':address2,
            'city': city,
            'zip': zip_code,
        })
        
        return True
        
    
    
    @api.multi
    def create_order_customer(self,res_obj,customer): 
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
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
            if 'country' in address:
                country = res_country_obj.search([('name','=',str(address['country_name']))])
                if country:
                    country_id = country.id
                else:
                    country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id

            if 'province' in address:
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:
                    state_id = state.id
                else:
                    state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
        customer_id = res_obj.create ({
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
            'gt_shopify_instance_id': self.id})
            
        
        
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