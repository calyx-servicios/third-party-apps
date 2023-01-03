from odoo.addons.mis_builder.models.aep import AccountingExpressionProcessor


def _get_company_rates_fixed(self, date):
    # get exchange rates for each company with its rouding
    company_rates = {}
    #target_rate = self.currency.with_context(date=date).rate
    for company in self.companies:
        if company.currency_id != self.currency:
            target_rate = self.currency.rate_ids.filtered(lambda x: x.name == date and x.company_id.id == company.id).rate
            rate = target_rate / company.currency_id.with_context(date=date).rate
        else:
            rate = 1.0
        company_rates[company.id] = (rate, company.currency_id.decimal_places)
    return company_rates

AccountingExpressionProcessor._get_company_rates = _get_company_rates_fixed