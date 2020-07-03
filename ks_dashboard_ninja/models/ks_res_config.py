from odoo import models, fields , api


class KsResConfig(models.TransientModel):
    _inherit = "res.config.settings"
    ks_responsive_enable = fields.Boolean(default ='1')



    @api.model
    def get_values(self):
        res = super(KsResConfig, self).get_values()
        res.update(
            ks_responsive_enable=self.env['ir.config_parameter'].sudo().get_param('ks_responsive_enable')
        )
        return res

    @api.multi
    def set_values(self):
        super(KsResConfig, self).set_values()
        for rec in self:
            self.env['ir.config_parameter'].sudo().set_param('ks_responsive_enable', rec.ks_responsive_enable)

