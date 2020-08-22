##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, models, fields
from datetime import date, timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # unreconciled_adl_ids = fields.One2many(
    #     'account.debt.line',
    #     'partner_id',
    #     domain=[
    #         ('reconciled', '=', False),
    #         ('account_id.deprecated', '=', False),
    #         ('account_id.internal_type', '=', 'receivable')]
    # )

    credit_overdue = fields.Monetary(
        compute='_compute_credit_overdue',
        string='Credit overdue',
        help="Total debt due of this customer."
    )

    @api.multi
    def _compute_credit_overdue(self):
        date_to = fields.Date.to_string(date.today() + timedelta(days=-1))
        for rec in self:
            rec.credit_overdue = rec.with_context(
                aged_balance=True, date_to=date_to).credit
