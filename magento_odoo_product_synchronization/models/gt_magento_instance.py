
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import logging
logger = logging.getLogger('product')


_logger = logging.getLogger(__name__)

class GtMagentoInstance(models.Model):
    _inherit='gt.magento.instance'

    def GtSynchroMagentoOdooSku(self):
        product_obj = self.env['product.product']
        store_obj = self.env['gt.magento.store']
        website_obj = self.env['gt.magento.website']

        if self.token:
            token = self.token
        else:
            token = self.generate_token()
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }

        #productos configurables (templates odoo)
        url = str(self.location)+"/rest/V1/products?searchCriteria[filterGroups][0][filters][0][field]=type_id& searchCriteria[filterGroups][0][filters][0][value]=configurable& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"
        response = requests.request("GET",url, headers=headers)
        product_list_configurable = json.loads(response.text)

        for product in product_list_configurable['items']:
            odoo_product_template = self.env['product.template'].search([('magento_sku', '=', product['sku']),('magento_template', '=', True),('active','=',True)])
            if len(odoo_product_template) == 1:
                if not odoo_product_template.magento_id:
                    odoo_product_template.magento_id = product['id']
            elif len(odoo_product_template) > 1:
                raise UserError(_('Hay mas de un producto con el SKU: ' + product['sku']))

        # productos simples (variantes odoo)
        url = str(self.location) + "/rest/V1/products?searchCriteria[filterGroups][0][filters][0][field]=type_id& searchCriteria[filterGroups][0][filters][0][value]=simple& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"
        response = requests.request("GET", url, headers=headers)
        product_list_simple = json.loads(response.text)
        for variante in product_list_simple['items']:
            odoo_product = self.env['product.product'].search([('product_type', '=', 'simple'), ('default_code', '=', variante['sku']),('magento_product', '=', True),('active','=',True)])
            if len(odoo_product) == 1:
                if not odoo_product.magento_id:
                    odoo_product.magento_id = variante['id']
            elif len(odoo_product) > 1:
                raise UserError(_('Hay mas de una variante de producto con el SKU: ' + variante['sku']))


        return True





