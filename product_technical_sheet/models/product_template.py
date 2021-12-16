# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = "product.template"

    pdf_tyc = fields.Binary(string="Add PDF", attachment=False)
    website_default = fields.Boolean('Default Website')
