from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"


    def call_sale_search_assistant(self):
                
        return {    
            'name': _("Search Assistant"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'search.assistant',
            'context':{'active_model':'sale.order','default_team_id': self.team_id.id},
            'active_id': self.id,
            'target': 'new',
        }
        
    