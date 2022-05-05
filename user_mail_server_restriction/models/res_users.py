# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    mail_server_ids = fields.Many2many(
        'ir.mail_server',
        string='Server Mail')

    default_mail_server_id = fields.Many2one(
        'ir.mail_server',
        string='Default Server Mail',
    )


