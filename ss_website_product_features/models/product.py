# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class feature_feature(models.Model):

	_name = 'feature.feature'


		
	name = fields.Char("Name")




class feature_product(models.Model):

	_name = 'feature.product'


		
	name = fields.Many2one('feature.feature', "Feature")
	desc = fields.Text("Description")
	product_id = fields.Many2one('product.template')
	
	
			
			
			
class product_template(models.Model):

	_inherit = 'product.template'


		
	feature_ids = fields.One2many('feature.product', 'product_id', "Features")
			



