from odoo import api, fields, models, _

class SearchAssistant(models.TransientModel):
    _inherit = "search.assistant"

    @api.multi
    def _get_domain_warehouse(self):
        responsible_user = self.env.user
        if responsible_user:
            warehouse_ids = responsible_user.stock_warehouse_ids.ids
            return [('id', 'in', warehouse_ids)]

    warehouse_id = fields.Many2one(domain=_get_domain_warehouse)