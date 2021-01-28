from odoo import api, fields, models, _

class SearchAssistant(models.TransientModel):

    def _get_sale_line_values(self, product_id, quantity, sale_order_id):
        line_obj = self.env['sale.order.line']
        values = {
            'name': product_id.name,
            'order_id': sale_order_id,
            'product_id': product_id.id,
            'template_id': product_id.product_tmpl_id.id,
            'variants_status_ok': True,
        }
        values.update(
            line_obj._prepare_add_missing_fields(values))
        values.update(
            {'product_uom_qty': quantity})
        return values