# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _get_domain_default_mail_server(self):
        for rec in self:
            if rec.mail_server_ids:
                return [('id', 'in', rec.mail_server_ids.ids)]

    mail_server_ids = fields.Many2many(
        'ir.mail_server',
        string='Server Mail')

    default_mail_server_id = fields.Many2one(
        'ir.mail_server',
        string='Default Server Mail',
        domain=_get_domain_default_mail_server
    )

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_domain_user_server_mail(self):
        responsible_user = self.env.user
        if responsible_user:
            mail_server_ids = responsible_user.mail_server_ids.ids
            return [('id', 'in', mail_server_ids)]

    mail_server_id = fields.Many2one(
        'ir.mail_server',
        string = 'Mail Server',
        domain=_get_domain_user_server_mail
    )

