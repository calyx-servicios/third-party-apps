import time
from openerp import api, fields, models


class ShopifyWizard(models.Model):
    _name = "shopify.wizard"
    
    
    gt_shopify_instance_ids = fields.Many2one('gt.shopify.instance',string='Select Instance')
    
    
    import_products = fields.Boolean('Import Products')
    import_inventory = fields.Boolean('Import Inventory')
    import_images = fields.Boolean('Import Images')
    import_orders = fields.Boolean('Import Orders')
    import_customer = fields.Boolean('Import Customer')
    
    update_shipment=fields.Boolean("Update Shipment")
    update_product=fields.Boolean('Update Product')
    update_stock=fields.Boolean('Update Stock')
    
    export_products = fields.Boolean('Export Products')
    export_images = fields.Boolean('Export Images')
    
    
    @api.model
    def default_get(self, fields):
        shop_obj = self.env['gt.shopify.instance']
        rec = super(ShopifyWizard, self).default_get(fields)
        if self._context.get('active_model') == 'gt.shopify.instance':
            shop_ids = shop_obj.browse(self._context.get('active_ids')[0])
            if shop_ids:
                rec.update({
                    'gt_shopify_instance_ids':shop_ids.id
                    })
        return rec    
  
    @api.one
    def import_magento_data(self):
        shop_obj = self.env['magento.store']
        product_obj = self.env['product.product']
        context = dict(self._context or {})
        active_id = context.get('active_ids')
        shop_id = shop_obj.browse(active_id)
        instance_ids=self.instance_ids
#     IMPORT FUNCTION
        if self.import_attribute_sets == True:
            instance_ids.import_att_set()
        if self.import_product_attributes == True:
            instance_ids.import_att_list()
        if self.import_categories == True:
            instance_ids.import_cat()
        if self.import_products == True:
            instance_ids.import_products()
        if self.import_inventory == True:
            'product inventory'
            instance_ids.import_products_stock(shop_id)
        
        if self.import_orders == True:
            shop_id.import_orders()
        
        if self.import_invoice == True:
            shop_id.import_invoice()
            
        if self.import_delivery == True:
            shop_id.import_picking()
          
#         if self.import_product_stock == True:
#             instance_ids.import_products_stock(shop_id)
#         if self.import_orders == True:
#             shop_id
#     UPDATE FUNCTION
        if self.update_stock == True:
            instance_ids.updateProductStock()
            
        if self.update_product == True:
            instance_ids.updateSimpleProductDashboard(shop_id)  
#             
#    EXPORT FUNCTION   
        if self.export_products:
            instance_ids.exportSimpleProductDashboard(shop_id)
        
        if self.export_shipment == True:
            shop_id.export_shipment()  
        
        if self.export_invoice == True:
            shop_id.export_invoice()       
#        if self.import_orders:
#            for shop_id in shop_ids:
#                shop_id.import_orders()
#        
#        if self.import_messages:
#            for shop_id in shop_ids:
#                shop_id.import_messages()
#                
#        if self.import_cart_rules:
#            for shop_id in shop_ids:
#                shop_id.import_cart_rules()
#        
#        if self.import_catalog_rules:
#            for shop_id in shop_ids:
#                shop_id.import_catalog_price_rules()
#                                        
#        if self.update_product_data:
#            for shop_id in shop_ids:
#                list_ids=self.env['product.listing'].search([('shop_id','>=',shop_id.id)])
#                product_ids=[list_id.product_id.id for list_id in list_ids if list_id.product_id]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['prestashop.upload.products'].create({}).upload_products(False,product_ids,presta_instance_id.id)
#        
#        if self.update_order_status:
#            for shop_id in shop_ids:
#                sale_ids=self.env['sale.order'].search([('shop_id','=',shop_id.id),('state','not in',('cancel','draft','sent'))])
#                sale_ids=[sale_id.id for sale_id in sale_ids]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['prestashop.upload.orders'].create({}).upload_orders(False,sale_ids,presta_instance_id)
#        
#        if self.update_categories:
#            for shop_id in shop_ids:
#                presta_instance_id=shop_id.prestashop_instance_id
#                prestashop=self.env['sale.shop'].browse(presta_instance_id.id).presta_connect_json()
#                categ_list=self.env['prestashop.category'].search([('shop_id','=',shop_id.id)])
##                 categ_list=[categ_id.id for categ_id in categ_list]
#                self.env['prestashop.upload.products'].upload_categories(prestashop,categ_list)        
#        
#        if self.update_cart_rules:
#            for shop_id in shop_ids:
#                cart_rule_ids=self.env['cart.rules'].search([('prestashop_id','=',shop_id.id)])
#                cart_rule_ids=[cart_id.id for cart_id in cart_rule_ids]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['upload.cart.rule'].create({}).upload_cart_rule(False,cart_rule_ids,presta_instance_id)
#        
#

        return True
    
    