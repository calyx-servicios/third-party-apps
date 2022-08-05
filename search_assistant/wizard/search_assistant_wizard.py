# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp
from ast import literal_eval

from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)


class SearchAssistantLine(models.TransientModel):
    """
    """
    _name = "search.assistant.line"
    _description = "Search Assistant Line"

    search_id = fields.Many2one('search.assistant', 'Search', required=True)
    selected = fields.Boolean(string='')
    description = fields.Char('Description')
    attribute_value_ids = fields.Many2many(
        'product.attribute.value', string='Attribute Values')
    product_id = fields.Many2one('product.product', string='Product')

    product_uom_qty = fields.Float(
        string='Quantity', digits=dp.get_precision('Product Price'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id', readonly=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision(
        'Product Price'), default=0.0)
    qty_available_today = fields.Float(string='Stock',)
    warehouse_id = fields.Many2one('stock.warehouse')
    brand_id = fields.Many2one('product.brand')

class SearchAssistant(models.TransientModel):
    """
    """
    _name = "search.assistant"
    _description = "Search Assistant"

    @api.model
    def _default_partner_id(self):
        """
        """
        return False

    @api.model
    def _default_warehouse_id(self):
        """
        """
        return False

    @api.model
    def _default_partner_readonly(self):
        """
        """
        return False

    @api.model
    def _default_stock_date(self):
        """
        """
        return fields.Datetime.now()

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search(
            [('company_id', '=', company)], limit=1)
        return warehouse_ids

    partner_readonly = fields.Boolean(
        string='Partner Readonly', default=_default_partner_readonly)

    partner_id = fields.Many2one(
        'res.partner', string='Partner', default=_default_partner_id, required=True)

    attribute_ids = fields.Many2many(
        'product.attribute', string='Product Attribute')

    attribute_value_ids = fields.Many2many(
        'product.attribute.value', string="Attribute Values")
    category_ids = fields.Many2many(
        'product.category', string="Product Categories")
    code = fields.Char(string='Code')

    description = fields.Char(string='Description',
                              help='Enter the description spaces split your query in \
                                    case you forgot how was your product description.')
    line_ids = fields.One2many(
        'search.assistant.line', 'search_id', string='Search Results')
    selected = fields.Boolean('')
    warehouse_id = fields.Many2one(
        'stock.warehouse', default=_default_warehouse_id)

    stock_date = fields.Datetime(
        'Stock Date', default=_default_stock_date, required=True)
    
    brand_ids = fields.Many2many(
        'product.brand', string="Product Brands")

    def make_domain(self, domain_name, code):
        """
        This function builds a domain spliting the code by spaces
        """
        domain_code = [(domain_name, 'ilike', '%')]
        if code:
            i = code.find(' ')
            domain_code = []
            while i != -1:
                domain_code.append((domain_name, 'ilike', code[0:i]))
                code = code[i+1:]
                i = code.find(' ')
            domain_code.append((domain_name, 'ilike', code))
        return domain_code

    def _get_domain_filter(self):
        """
        """
        _logger.debug('====> filter activated ====>')
        _logger.debug(self._context.get('active_model'))
        product_attribute_obj = self.env['product.attribute.value']
        domain = []

        attribute_ids = list(set(self.attribute_ids.ids))
        attribute_values_ids = list(set(self.attribute_value_ids.ids))
        category_ids = list(set(self.category_ids.ids))
        brand_ids = list(set(self.brand_ids.ids))
        description = self.description
        code = self.code

        if description and len(description) > 0:
            for description_domain in self.make_domain('name', description):
                domain.append(description_domain)
        if code and len(code) > 0:
            for code_domain in self.make_domain('default_code', code):
                domain.append(code_domain)

        if len(brand_ids) > 0:
            product_template_obj = self.env['product.template']
            product_ids = product_template_obj.search(
                    [('product_brand_id', 'in', brand_ids)]).ids
            domain.append(('product_tmpl_id', 'in', product_ids))

        if len(attribute_values_ids) > 0:
            domain.append(('attribute_value_ids', 'in', attribute_values_ids))
        else:
            if len(attribute_ids) > 0:
                attribute_ids = product_attribute_obj.search(
                    [('attribute_id', 'in', attribute_ids)]).ids
                domain.append(('attribute_value_ids', 'in', attribute_ids))

        if len(category_ids) > 0:
            domain.append(('categ_id', 'in', category_ids))
        _logger.debug('====> DOMAIN ====> %s' % domain)
        return domain

    def _get_selected_products(self):
        return None

    def _search(self, selected_products=None):
        product_obj = self.env['product.product']
        self.line_ids = False
        domain = self._get_domain_filter()
        if len(domain) > 0:
            product_ids = product_obj.search(domain)
            line_ids = []
            for product in product_ids:
                selected = self.selected
                if not self.selected and selected_products:
                    selected = selected_products and product.id in selected_products
                
                available_qty = self.env['stock.quant']._get_available_quantity(product, self.warehouse_id.view_location_id)
                line_ids.append((0, 0, {
                    'selected': selected,
                    'product_id': product.id,
                    'attribute_value_ids': [(6, 0, product.attribute_value_ids.ids)],
                    'price_unit': product.lst_price,
                    'qty_available_today': product.qty_available_not_res,
                    'description': product.description or '',
                    'brand_id': product.product_tmpl_id.product_brand_id
                }))

            self.line_ids = line_ids

    @api.onchange('attribute_ids', 'attribute_value_ids', 'description', 'selected', 'category_ids', 'code', 'warehouse_id', 'stock_date', 'brand_ids')
    def search(self):
        """
        """
        self._search(selected_products=None)
