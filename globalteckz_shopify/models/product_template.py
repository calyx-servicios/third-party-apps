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
import itertools
import psycopg2
#from odoo.exceptions import ValidationError, except_orm
import logging
logger = logging.getLogger('product')

class ProductTemplate(models.Model):
    _inherit='product.template'
    
    
    gt_published_scope = fields.Many2one('gt.published.scope', string='Published Scope')
    gt_shopify_description = fields.Text(string='Shopify Description')
    gt_vendor = fields.Many2one('gt.shopify.vendor',string='Vendor')
    gt_product_id = fields.Char(string='Product ID')
    gt_requires_shipping = fields.Boolean(string='Requires Shipping')
    gt_product_tags = fields.Many2many('gt.shopify.product.tags', 'tags_product_rel', 'tags_id', 'tags', string='Product Tags')
    gt_shopify_product = fields.Boolean(string='Shopify Product')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_product_image_id = fields.One2many('gt.product.photo', 'gt_product_temp_id', string='Product Images')
    gt_shopify_exported = fields.Boolean(string='Shopify Exported')
    gt_shopify_product_type = fields.Many2one('gt.shopify.product.type',string='Product Type')
    
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
            if len(products['options']) == 1:
                for options in products['options']:
                    if str(options['name']) != 'Title':
                        print ('options++++++=', options)
            else:
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
            }
            product_id = self.search([('gt_product_id','=',str(products['id'])),('gt_shopify_instance_id','=',instance.id),('gt_shopify_product','=',True)])
    #        if len(product_id) > 0 :
    #            product_id.write(vals)
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
                'attribute_line_ids': variant,
                'gt_shopify_exported': True,
                'gt_shopify_product_type' : type_id,
            }
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
    def create_variant_ids(self):
        Product = self.env["product.product"]
        AttributeValues = self.env['product.attribute.value']
        for tmpl_id in self.with_context(active_test=False):
            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            variant_alone = tmpl_id.attribute_line_ids.filtered(lambda line: len(line.value_ids) == 1).mapped('value_ids')
            for value_id in variant_alone:
                updated_products = tmpl_id.product_variant_ids.filtered(lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
                updated_products.write({'attribute_value_ids': [(4, value_id.id)],'default_code': tmpl_id.gt_product_id,'gt_shopify_product':tmpl_id.gt_shopify_product,'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id})

            # iterator of n-uple of product.attribute.value *ids*
            variant_matrix = [
                AttributeValues.browse(value_ids)
                for value_ids in itertools.product(*(line.value_ids.ids for line in tmpl_id.attribute_line_ids if line.value_ids[:1].attribute_id.create_variant))
            ]

            # get the value (id) sets of existing variants
            existing_variants = {frozenset(variant.attribute_value_ids.ids) for variant in tmpl_id.product_variant_ids}
            # -> for each value set, create a recordset of values to create a
            #    variant for if the value set isn't already a variant
            to_create_variants = [
                value_ids
                for value_ids in variant_matrix
                if set(value_ids.ids) not in existing_variants
            ]

            # check product
            variants_to_activate = self.env['product.product']
            variants_to_unlink = self.env['product.product']
            for product_id in tmpl_id.product_variant_ids:
                if not product_id.active and product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) in variant_matrix:
                    variants_to_activate |= product_id
                elif product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) not in variant_matrix:
                    variants_to_unlink |= product_id
            if variants_to_activate:
                variants_to_activate.write({'active': True})

            # create new product
            for variant_ids in to_create_variants:
                new_variant = Product.create({
                    'product_tmpl_id': tmpl_id.id,
                    'attribute_value_ids': [(6, 0, variant_ids.ids)],
                    'default_code': tmpl_id.gt_product_id,
                    'gt_shopify_product':tmpl_id.gt_shopify_product,
                    'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id,
                })

            # unlink or inactive product
            for variant in variants_to_unlink:
                try:
                    with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                        variant.unlink()
                # We catch all kind of exception to be sure that the operation doesn't fail.
                except (psycopg2.Error, except_orm):
                    variant.write({'active': False})
                    pass
        return True

    
    
    
#    @api.multi
#    def create_variant_ids(self):
#        Product = self.env["product.product"]
#        for tmpl_id in self.with_context(active_test=False):
#            # adding an attribute with only one value should not recreate product
#            # write this attribute on every product to make sure we don't lose them
#            variant_alone = tmpl_id.attribute_line_ids.filtered(lambda line: len(line.value_ids) == 1).mapped('value_ids')
#            for value_id in variant_alone:
#                updated_products = tmpl_id.product_variant_ids.filtered(lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
#                updated_products.write({'attribute_value_ids': [(4, value_id.id)],'default_code': tmpl_id.gt_product_id,'gt_shopify_product':tmpl_id.gt_shopify_product,'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id})
#
#            # list of values combination
#            existing_variants = [set(variant.attribute_value_ids.ids) for variant in tmpl_id.product_variant_ids]
#            variant_matrix = itertools.product(*(line.value_ids for line in tmpl_id.attribute_line_ids if line.value_ids and line.value_ids[0].attribute_id.create_variant))
#            variant_matrix = map(lambda record_list: reduce(lambda x, y: x+y, record_list, self.env['product.attribute.value']), variant_matrix)
#            to_create_variants = filter(lambda rec_set: set(rec_set.ids) not in existing_variants, variant_matrix)
#            # check product
#            variants_to_activate = self.env['product.product']
#            variants_to_unlink = self.env['product.product']
#            for product_id in tmpl_id.product_variant_ids:
#                if not product_id.active and product_id.attribute_value_ids in variant_matrix:
#                    variants_to_activate |= product_id
#                elif product_id.attribute_value_ids not in variant_matrix:
#                    variants_to_unlink |= product_id
#            if variants_to_activate:
#                variants_to_activate.write({'active': True})
#
#            # create new product
#            for variant_ids in to_create_variants:
#                new_variant = Product.create({
#                    'product_tmpl_id': tmpl_id.id,
#                    'attribute_value_ids': [(6, 0, variant_ids.ids)],
#                    'default_code': tmpl_id.gt_product_id,
#                    'gt_shopify_product':tmpl_id.gt_shopify_product,
#                    'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id,
#                })
#            
#            # unlink or inactive product
#            for variant in variants_to_unlink:
#                try:
#                    with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
#                        variant.unlink()
#                # We catch all kind of exception to be sure that the operation doesn't fail.
#                except (psycopg2.Error, except_orm):
#                    variant.write({'active': False})
#                    pass
#        return True
#    
#    
    
    @api.multi
    def gt_export_shopify_product(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        #product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', False),('gt_shopify_product','=',True)])
        ids = product_tmpl_obj.search([('id','=', 7)])
        ids.write({'gt_shopify_exported':True})
        self._cr.commit()
        for products in self:
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