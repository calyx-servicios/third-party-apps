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

from odoo import fields,api,models, tools
from datetime import date
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import requests
import json
import itertools
import psycopg2
import base64
import urllib
#from odoo.exceptions import ValidationError, except_orm
import logging
logger = logging.getLogger('product')

class ProductTemplate(models.Model):
    _inherit='product.template'
    
    
    gt_published_scope = fields.Many2one('gt.published.scope', string='Published Scope')
    gt_shopify_description = fields.Html(string='Shopify Description')
    gt_vendor = fields.Many2one('gt.shopify.vendor',string='Vendor')
    gt_product_id = fields.Char(string='Product ID')
    gt_requires_shipping = fields.Boolean(string='Requires Shipping')
    gt_product_tags = fields.Many2many('gt.shopify.product.tags', 'tags_product_rel', 'tags_id', 'tags', string='Product Tags')
    gt_shopify_product = fields.Boolean(string='Shopify Product')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_product_image_id = fields.One2many('gt.product.photo', 'gt_product_temp_id', string='Product Images')
    gt_shopify_exported = fields.Boolean(string='Shopify Exported')
    gt_shopify_product_type = fields.Many2one('gt.shopify.product.type',string='Product Type')
    gt_shopify_active = fields.Boolean(string ='Active Publication')
    
    @api.multi
    def update_variant_ids(self,shopify_instance_id):
        
        shopify_url = str(shopify_instance_id.gt_location)
        api_key = str(shopify_instance_id.gt_api_key)
        api_pass = str(shopify_instance_id.gt_password)
        #shop_url = shopify_url + 'admin/products.json'
        shop_url = shopify_url + 'admin/products/' + str(self.gt_product_id) + '.json'
        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_rs=json.loads(response.text)
        product_items = product_rs['product']
        product_obj = self.env['product.product']

        if 'variants' in product_items:
            for variant in product_items['variants']:
                if 'id' in variant:
                    product_ids = product_obj.search(['|',('product_tmpl_id.gt_product_id','=',product_items['id']),('default_code','=',variant['product_id'])])
                    if product_ids:                      
                        if variant['option3'] != None:
                            for product in product_ids:
                                variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name, product.attribute_value_ids[2].name ]
                                if (variant['option1'] in variantes) and (variant['option2'] in variantes) and (variant['option3'] in variantes):
                                    product.write({'gt_product_id': variant['id']})
                                    product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                    product.write({'gt_product_inventory_tracked': product._is_inventory_tracking(shopify_instance_id)})
                                    product.write({'gt_shopify_exported': True})
                                    if variant['compare_at_price'] != None:
                                        if variant['compare_at_price'] != 0 and float(variant['compare_at_price']) > float(variant['price']): 
                                            product.write({'gt_product_price_compare': variant['compare_at_price']})
                        elif variant['option2'] != None:
                            for product in product_ids:
                                variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name]
                                if (variant['option1'] in variantes) and (variant['option2'] in variantes):
                                    product.write({'gt_product_id': variant['id']})
                                    product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                    product.write({'gt_product_inventory_tracked': product._is_inventory_tracking(shopify_instance_id)})
                                    product.write({'gt_shopify_exported': True})
                                    if variant['compare_at_price'] != None:    
                                        if variant['compare_at_price'] != 0 and float(variant['compare_at_price']) > float(variant['price']): 
                                            product.write({'gt_product_price_compare': variant['compare_at_price']})
                        elif variant['option1'] != None:
                            for product in product_ids:
                                if product.attribute_value_ids.name == variant['option1'] :
                                    product.write({'gt_product_id': variant['id']})
                                    product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                    product.write({'gt_product_inventory_tracked': product._is_inventory_tracking(shopify_instance_id)})
                                    product.write({'gt_shopify_exported': True})
                                    if variant['compare_at_price'] != None:
                                        if variant['compare_at_price'] != 0 and float(variant['compare_at_price']) > float(variant['price']): 
                                            product.write({'gt_product_price_compare': variant['compare_at_price']})
                        else:
                            for product in product_ids:
                                product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                product.write({'gt_product_inventory_tracked': product._is_inventory_tracking(shopify_instance_id)})
                                product.write({'gt_shopify_exported': True})
                                if variant['compare_at_price'] != None:
                                    if variant['compare_at_price'] != 0 and float(variant['compare_at_price']) > float(variant['price']): 
                                        product.write({'gt_product_price_compare': variant['compare_at_price']})


    @api.multi
    def _get_product_active(self,instance):

        shopify_url = str(instance.gt_location)
        api_key = str(instance.gt_api_key)
        api_pass = str(instance.gt_password)
        shop_url = shopify_url + 'admin/api/2021-01/products.json?status=active&ids=' + str(self.gt_product_id)
        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_rs=json.loads(response.text)
        if len(product_rs['products'])>0:
            return True
        else:
            return False

    @api.multi
    def gt_create_product_template(self,products,instance,log_id):
        product_obj = self.env['product.product']
        scope_obj = self.env['gt.published.scope']
        vendor_obj = self.env['gt.shopify.vendor']
        tags_obj = self.env['gt.shopify.product.tags']
        product_attribute_obj = self.env['product.attribute']
        product_attribute_option_obj = self.env['product.attribute.value']
        product_type_obj = self.env['gt.shopify.product.type']
        log_line_obj = self.env['shopify.log.details']
        scopes = []
        vendors = []
        tags_lst = []
        type_id = []
        
        try:
            if 'product_type' in products:
                product_type_id = product_type_obj.search([('name','=',products['product_type']),('gt_shopify_instance_id','=',instance.id)])
                if len(product_type_id) > 0 :
                    type_id = product_type_id.id
                else:
                    type_id = product_type_obj.create({'name': products['product_type'], 'gt_shopify_instance_id':instance.id }).id
            if 'title' in products:
                scope_id = scope_obj.search([('name','=',products['published_scope']),('gt_shopify_instance_id','=',instance.id)])
                if len(scope_id) > 0 :
                   scopes =  scope_id.id
                else:
                    scopes = scope_obj.create({'name':str(products['published_scope']),'gt_shopify_instance_id':instance.id}).id
            if 'vendor' in products:
                vendor_id = vendor_obj.search([('name','=',products['vendor']),('gt_shopify_instance_id','=',instance.id)])
                if len(scope_id) > 0 :
                   vendors =  vendor_id.id
                else:
                    vendors = vendor_obj.create({'name':str(products['vendor']),'gt_shopify_instance_id':instance.id}).id
            if 'tags' in products:
                if str(products['tags']) != '':
                    tags_split = products['tags'].split(',')
                    for tags in tags_split:
                        tags_id = tags_obj.search([('name','=',str(tags)),('gt_shopify_instance_id','=',instance.id)])
                        if len(tags_id) > 0:
                            tags_lst.append(tags_id.id)
                        else:
                            tags_id = tags_obj.create({'name':str(tags),'gt_shopify_instance_id':instance.id})
                            tags_lst.append(tags_id.id)
            variant = []
            
            def _variants(self):

                if len(self) == 1:
                    return len(self[0]['values'])
                elif len(self) == 2:
                    return len(self[1]['values'])
                elif len(self) == 3:
                    return len(self[2]['values'])    
                else:  
                    return 1

            for options in products['options']:
                attribute_id = []
                att_search = []
                value_search = []
                if 'name' in options:
                    att_id = product_attribute_obj.search([('name','=',str(options['name']))])
                    att_search.append(att_id.id)
                    if att_id:
                        attribute_id = att_search[0]
                    else:
                        attribute_id = product_attribute_obj.create({'name': str(options['name']),'create_variant': True}).id
                if 'values' in options:
                    value_list = []
                    value_id = []
                    for values in options['values']:
                        value = product_attribute_option_obj.search([('attribute_id','=',attribute_id),('name','=',values)])
                        value_search.append(value.id)
                        if value:
                            value_id = value
                        else:
                            value_id = product_attribute_option_obj.create({'name': values,'attribute_id': attribute_id})
                        value_list.append(value_id.id)

                    variant.append((0,0,{'attribute_id': attribute_id,'value_ids': [(6, 0,value_list)]}))
            
            vals = {
                'name': products['title'] if 'title' in products else '',
                'type': "product",
                'gt_shopify_product':True,
                'gt_published_scope' : scopes,
                'gt_shopify_description': products['body_html'] if 'body_html' in products else '',
                'gt_vendor' : vendors,
                'gt_product_id' : str(products['id']) if 'id' in products else '',
                'gt_product_tags': [(6, 0, tags_lst)],
                'gt_shopify_instance_id':instance.id,
                'attribute_line_ids': variant,
                'gt_shopify_exported': True,
                'gt_shopify_product_type' : type_id,
                'gt_shopify_active' : self._get_product_active(instance),
            }
            product_id = self.search([('gt_product_id','=',str(products['id'])),('gt_shopify_instance_id','=',instance.id),('gt_shopify_product','=',True)])

            if not product_id:
                self.create(vals)
            else:
                vals = {
                    'name': products['title'] if 'title' in products else '',
                    'type': "product",
                    'gt_shopify_product':True,
                    'gt_published_scope' : scopes,
                    'gt_shopify_description': products['body_html'] if 'body_html' in products else '',
                    'gt_vendor' : vendors,
                    'gt_shopify_instance_id':instance.id,
                    'gt_shopify_exported': True,
                    'gt_shopify_product_type' : type_id,
                    'gt_shopify_active' : product_id._get_product_active(instance)
                }
                product_id.write(vals)
                product_id.update_variant_ids(instance)
            
            self._cr.commit()
            

            if 'variants' in products and len(products['variants']) > 1:
                value_id1 = []
                value_id2 = []
                value_id3 = []
                product_product = []
                for variant in products['variants']:
                    value_id_list = []
                    if 'option1' in variant and variant['option1'] != None and variant['option1'] != 'Default Title':

                        value_id1 = product_attribute_option_obj.search([('name','=', str(variant['option1']))])

                        value_id_list.append(value_id1[0].id)

                    if 'option2' in variant and variant['option2'] != None:

                        value_id2 = product_attribute_option_obj.search([('name','=', str(variant['option2']))])

                        value_id_list.append(value_id2[0].id)

                    if 'option3' in variant and variant['option3'] != None:

                        value_id3 = product_attribute_option_obj.search([('name','=', str(variant['option3']))])        

                        value_id_list.append(value_id3[0].id)

                    if value_id1 and value_id2 and value_id3:

                        product_product = product_obj.search([('default_code','=',str(products['id'])),('attribute_value_ids','in',[value_id1[0].id,value_id2[0].id,value_id3[0].id])])

                    elif value_id1 and value_id2:

                        product_product = product_obj.search([('default_code','=',str(products['id'])),('attribute_value_ids','in',[value_id1[0].id,value_id2[0].id])])

                    elif value_id1 and value_id2:

                        product_product = product_obj.search([('default_code','=',str(products['id'])),('attribute_value_ids','in',[value_id1[0].id])])

                    if product_product:
                        for product_ids in product_product:
                            attribute_list = []

                            for att_idss in product_ids.attribute_value_ids:
                                attribute_list.append(att_idss.id)
                            if sorted(attribute_list, key=int) == sorted(value_id_list, key=int):
                                product_ids.update_variant(variant,instance,log_id)
            else:
                for variant in products['variants']:
                    product_product = product_obj.search([('default_code','=',str(variant['product_id']))])
                    if product_product:
                        product_product.update_variant(variant,instance,log_id)

            

        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_line_obj.create({'name':'Create Product Template','description':exc,'create_date':date.today(),
                                      'shopify_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 
        return True
    

    @api.multi
    def update_product_stock(self):

        product_obj = self.env['product.product']
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        product_ids = product_obj.search([('product_tmpl_id.gt_shopify_exported','=', True),('product_tmpl_id.id', '=', self.id )])
        for products in product_ids:
            qty_available = self.env['stock.quant'].search([('product_id','=',products.id),('location_id','=',self.gt_shopify_instance_id.gt_workflow_id.stock_location_id.id)])
            quantity = qty_available.quantity - qty_available.reserved_quantity
            if quantity >= 0:
                vals =  {
                    "location_id": products._get_primary_stock_location(),
                    "inventory_item_id": products.gt_product_inventory_id,
                    "available": int(quantity),
                }
                shop_url = shopify_url + 'admin/api/2021-01/inventory_levels/set.json'
                response = requests.post(shop_url,auth=(api_key,api_pass),data=vals)

    @api.multi
    def update_product_shopify(self):

        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        
        tag = ''
        if len(self.gt_product_tags) == 1:
            tag = str(self.gt_product_tags.name)
        else:
            for tags in self.gt_product_tags:
                tag += str(tags.name)+','         
        
        vals = {
            "product": {
            "id": int(self.gt_product_id),
            "title": str(self.name),
            "status": "active" if self.gt_shopify_active else "draft",
            "tags": tag,
            "body_html": self.gt_shopify_description,
          }  
        }

        shop_url = shopify_url + '/admin/api/2021-01/products/'+ str(self.gt_product_id) +'.json'
        response = requests.put(shop_url,auth=(api_key,api_pass),data=json.dumps(vals), headers={'Content-Type': 'application/json'})

        for product in self.product_variant_ids:
            if product.gt_product_id:
                if product.gt_product_price_compare != 0:
                    vals = {
                      "variant": {
                        "id": int(product.gt_product_id),
                        "price": product.lst_price,
                        "compare_at_price": product.gt_product_price_compare,
                      }
                    }                
                else:
                    vals = {
                      "variant": {
                        "id": int(product.gt_product_id),
                        "price": product.lst_price,
                      }
                    }                
                shop_url = shopify_url + '/admin/api/2021-01/variants/'+ str(product.gt_product_id) +'.json'
                response = requests.put(shop_url,auth=(api_key,api_pass),data=json.dumps(vals), headers={'Content-Type': 'application/json'})

     
    @api.multi
    def update_product_odoo(self):
        
        log_id = self.env['shopify.log.details']
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        
        shop_url = shopify_url + 'admin/products/' + str(self.gt_product_id) + '.json'

        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_item = json.loads(response.text)
        
        self.gt_create_product_template(product_item['product'], self.gt_shopify_instance_id, log_id)


    @api.multi
    def update_images_shopify(self):
        
        log_id = self.env['shopify.log.details']
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        
        shop_url = shopify_url + 'admin/products/'+str(self.gt_product_id)+'/images.json'
        response = requests.get( shop_url,auth=(api_key,api_pass))
        product_rs=json.loads(response.text)
        product_items = product_rs['images']
        photo_obj = self.env['gt.product.photo']
        product_obj = self.env['product.product']
        log_line_obj = self.env['shopify.log.details']

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
                        'gt_product_temp_id': self.id,
                        }
                    photo_id = photo_obj.search([('gt_image_id','=',image['id']),('gt_product_temp_id','=',self.id)])
                    if photo_id:
                        photo_id.write(vals)
                    else:
                        photo_obj.create(vals)
                    image_id_medium = self.write({'image_medium':image_path})
                    image_id_small = self.write({'image_small':image_path})
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

    @api.multi
    def gt_export_shopify_product(self):

        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)

        if not self.gt_shopify_instance_id:
            raise ValidationError('Debe seleccionar una instancia de Shopify para poder exportar el producto a la tienda.')

        for products in self:

            tag = ''
            if len(products.gt_product_tags) == 1:
                tag = str(products.gt_product_tags.name)
            else:
                for tags in products.gt_product_tags:
                    tag += str(tags.name)+',' 

            if len(products.product_variant_ids) > 0 and not products.gt_product_id:

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
                    if len(variants.attribute_value_ids) <= 3:
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
                            "barcode": str(variants.barcode),
                            "inventory_management": "shopify",
                            "option1": option1,
                            "option2": option2,
                            "option3": option3,
                          }

                    list_variant.append(vals_variant)


                if len(option1_list) > 0:
                    vals_option = {"name": attribute1, "values": option1_list}
                    options.append(vals_option)
                if len(option2_list) > 0:
                    vals_option = { "name": attribute2, "values": option2_list}
                    options.append(vals_option)
                if len(option3_list) > 0:
                    vals_option = {"name": attribute3, "values": option3_list}
                    options.append(vals_option)

                vals = {
                    "product": {
                      "title": str(products.name),
                      "body_html": str(products.gt_shopify_description),
                      "product_type": str(products.gt_shopify_product_type.name),
                      "inventory_management": "shopify",
                      "tags": tag,
                      "options": options,
                      "variants": list_variant,
                      "status": "active" if products.gt_shopify_active else "draft",
                    }
                  }

                payload= json.dumps(vals)
                shop_url = shopify_url + 'admin/api/2021-01/products.json'
                response = requests.post( shop_url,auth=(api_key,api_pass), data=payload, headers={'Content-Type': 'application/json',})

                if str(response) == '<Response [201]>':
                    prod_id = response.json()["product"]["id"]
                    products.write({'gt_shopify_exported': True, 'gt_product_id': prod_id})

                    shop_url = shopify_url + 'admin/api/2021-01/products/'+str(prod_id)+'/variants.json'
                    response = requests.get(shop_url,auth=(api_key,api_pass))
                    variants = json.loads(response.text)

                    
                    products_id = self.env['product.product'].search([('product_tmpl_id.gt_product_id','=',prod_id)])

                    for product_id in products_id:

                        for variant in variants['variants']:

                            if variant['option3'] != None:
                                for product in product_id:
                                    variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name, product.attribute_value_ids[2].name ]
                                    if (variant['option1'] in variantes) and (variant['option2'] in variantes) and (variant['option3'] in variantes):
                                        product.write({'gt_product_id': variant['id']})
                                        product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                        product.write({'gt_shopify_exported': True})
                                        product.write({'gt_shopify_instance_id': self.gt_shopify_instance_id.id})
                            elif variant['option2'] != None:
                                for product in product_id:
                                    variantes = [product.attribute_value_ids[0].name,product.attribute_value_ids[1].name]
                                    if (variant['option1'] in variantes) and (variant['option2'] in variantes):
                                        product.write({'gt_product_id': variant['id']})
                                        product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                        product.write({'gt_shopify_exported': True})
                                        product.write({'gt_shopify_instance_id': self.gt_shopify_instance_id.id})
                            elif variant['option1'] != None:
                                for product in product_id:
                                    if product.attribute_value_ids.name == variant['option1'] :
                                        product.write({'gt_product_id': variant['id']})
                                        product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                        product.write({'gt_shopify_exported': True})
                                        product.write({'gt_shopify_instance_id': self.gt_shopify_instance_id.id})
                            else:
                                product.write({'gt_product_inventory_id': variant['inventory_item_id']})
                                product.write({'gt_shopify_exported': True})
                                product.write({'gt_shopify_instance_id': self.gt_shopify_instance_id.id})

        return True
    

class GtPublishedScope(models.Model):
    _name='gt.published.scope'
    
    name = fields.Char(string='Scope name')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
class GtShopifyVendor(models.Model):
    _name = 'gt.shopify.vendor'
        
    name = fields.Char(string='Vendor name')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
    
class GtShopifyProductTags(models.Model):
    _name = 'gt.shopify.product.tags'
    
    name = fields.Char(string='Product Tags')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
class GtShopifyProductType(models.Model):
    _name = 'gt.shopify.product.type'
    
    name = fields.Char(string='Product Type')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')