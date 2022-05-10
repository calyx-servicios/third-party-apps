# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_pos_product_operations = fields.Boolean(string='Allow Product Operations')
    allow_edit_product  = fields.Boolean(string='Allow user to edit/create product from pos')

class ProductProduct(models.Model):
    _inherit = 'product.product'
        
    @api.model
    def create_from_ui(self, product):
        # image is a dataurl, get the data after the comma
        product_id = product.pop('id', False)
        product_get_id = self.browse(product_id)
        if product_id:
            if product_get_id.product_tmpl_id.attribute_line_ids:
                if product.get('list_price') != '':
                    if '.' in product.get('list_price'):
                        product.mapped('attribute_value_ids.price_ids')
                        product['price_extra'] = product.get('list_price')
                        price = product_get_id.list_price
                        product['lst_price'] = price + int(product['price_extra'])
                    else:
                        product['price_extra'] = product.get('list_price').replace(',','.')
                        AttributePrice = self.env['product.template.attribute.value']
                        for attr in product_get_id.product_template_attribute_value_ids.ids:
                            prices = AttributePrice.search([('id', '=', attr), ('product_tmpl_id', '=', product_get_id.product_tmpl_id.id)])
                            if prices:
                                prices.write({'price_extra': int(product['price_extra'])/len(product_get_id.product_template_attribute_value_ids.ids)})
                        product['lst_price'] = product_get_id.list_price + product_get_id.price_extra
                else:
                        product['lst_price'] = product_get_id.lst_price
            else:
                if product.get('list_price') != '':
                    product['lst_price'] = product.get('list_price')
                else:
                    product['lst_price'] = product_get_id.lst_price
        else:
            if '.' in product.get('list_price'):
                product['list_price'] = product.get('list_price')
            else:
                product['list_price'] = product.get('list_price').replace(',','.')

        if product.get('standard_price') != '':
            if '.' in product.get('standard_price'):        
                product['standard_price'] = product.get('standard_price')       
            else:       
                product['standard_price'] = product.get('standard_price').replace(',','.')
        else:
            product['standard_price'] = product_get_id.standard_price

        if product.get('price') != '':         
            if '.' in product.get('price'):
                product['standard_price'] = product.get('price')     
            else:
                product['standard_price'] = product.get('price').replace(',','.')
        else:
            product['standard_price'] = product_get_id.standard_price                

        if ('(') in product.get('display_name'):
             name = product.get('display_name').split('(')
             product['name'] = name[0]
        else:
            product['name'] = product.get('display_name')
        product['barcode'] = product.get('barcode')
        product['available_in_pos'] = True
        if product.get('pos_categ_id') != False:
            product['categ_id'] =product.get('pos_categ_id')
        else:
            product['pos_categ_id'] =product_get_id.pos_categ_id.id
        str_b = False
        if product.get('image_1920') != None:
            str_b = product.get('image_1920').strip("data:image/png;base64,")
            product['image_1920'] ="i"+str_b
            if product_id:  # Modifying existing product
                self.browse(product_id).write(product)
            else:
                product_id = self.create({'name':product.get('display_name'),
                                        'available_in_pos' : True,
                                        'barcode':product.get('barcode'),
                                        'lst_price':product.get('list_price'),
                                        'standard_price':product.get('standard_price'),
                                        'pos_categ_id' :product.get('pos_categ_id'),
                                        'image_1920':"i"+str_b
                                            })
        else:
            if product_id:  # Modifying existing product
                self.browse(product_id).write(product)
            else:
                product_id = self.create({
                                        'name':product.get('display_name'),
                                        'available_in_pos' : True,
                                        'barcode':product.get('barcode'),
                                        'lst_price':product.get('list_price'),
                                        'standard_price':product.get('standard_price'),
                                        'pos_categ_id' :product.get('pos_categ_id')
                                            })
        return product_id
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    