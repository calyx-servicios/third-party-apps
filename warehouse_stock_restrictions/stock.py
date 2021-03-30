# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    stock_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Warehouse')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_domain_warehouse(self):
        responsible_user = self.env.user
        if responsible_user:
            warehouse_ids = responsible_user.stock_warehouse_ids.ids
            return [('id', 'in', warehouse_ids)]

    warehouse_id = fields.Many2one(domain=_get_domain_warehouse)

