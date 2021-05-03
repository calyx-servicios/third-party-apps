# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderMailWizard(models.TransientModel):
    _inherit = 'sale.order.mail.wizard'

    @api.multi
    def _get_domain_user_server_mail(self):
        responsible_user = self.env.user
        if responsible_user:
            mail_server_ids = responsible_user.mail_server_ids.ids
            return [('id', 'in', mail_server_ids)]

    mail_server_id = fields.Many2one(
        default=lambda self: self.env.user.default_mail_server_id,
        domain=_get_domain_user_server_mail
    )