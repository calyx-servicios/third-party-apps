# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ConfigSign(models.Model):
    _name = 'config.sign'
    _description = "Sign Configuration"

    sign_position_a = fields.Integer()
    sign_position_b = fields.Integer()
    sign_position_c = fields.Integer()
    sign_position_d = fields.Integer()