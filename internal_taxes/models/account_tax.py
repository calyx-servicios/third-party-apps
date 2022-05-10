# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = "account.tax"
    
    amount_type = fields.Selection(selection_add=[('internal_taxes','Internal Taxes'),('ad_emergency','Ad. Emergency'), ('fet','FET')])
    
    sale_price_afip = fields.Float(string="Informed sale price AFIP",digits=(16, 4),)
    production_cost = fields.Float(string="Production cost",digits=(16, 4),)
    wholesale_price = fields.Float(string="Wholesaler's price",digits=(16, 4),)
    retail_price = fields.Float(string="Retail price",digits=(16, 4),) 
    fixed_fet = fields.Float(string="Fixed Fet %",digits=(16, 5),)
    
    wholesale_net_sale_price = fields.Float(
        string="Wholesaler's Net Selling Price",
        digits=(16, 4),
        compute="_compute_wholesale_net_sale_price",
        store=True,
    )
    wholesale_iva = fields.Float(
        string="Wholesale IVA",
        digits=(16, 4),
        compute="_compute_wholesale_iva",
        store=True,
    )
    wholesale_internal = fields.Float(
        string="Wholesale Internal",
        digits=(16, 4),
        compute="_compute_wholesale_internal",
        store=True,
    )
    wholesale_ad_emergency = fields.Float(
        string="Wholesale Ad. Emergency",
        digits=(16, 4),
        compute="_compute_wholesale_ad_emergency",
        store=True,
    )
    wholesale_fet = fields.Float(
        string="Wholesale FET",
        digits=(16, 4),
        compute="_compute_wholesale_fet",
        store=True,
    )
    wholesale_total_sale_price_taxes = fields.Float(
        string="Wholesale total sales price with taxes",
        digits=(16, 4),
        compute="_compute_wholesale_total_sale_price_taxes",
        store=True,
    )
    
    
    retail_net_sale_price = fields.Float(
        string="Retail Net Selling Price",
        digits=(16, 4),
        compute="_compute_retail_net_sale_price",
        store=True,
    )
    retail_iva = fields.Float(
        string="Retail IVA",
        digits=(16, 4),
        compute="_compute_retail_iva",
        store=True,
    )
    retail_internal = fields.Float(
        string="Retail Internal",
        digits=(16, 4),
        compute="_compute_retail_internal",
        store=True,
    )
    retail_ad_emergency = fields.Float(
        string="Retail Ad. Emergency",
        digits=(16, 4),
        compute="_compute_retail_ad_emergency",
        store=True,
    )
    retail_fet = fields.Float(
        string="Retail FET",
        digits=(16, 4),
        compute="_compute_retail_fet",
        store=True,
    )
    retail_total_sale_price_taxes = fields.Float(
        string="Retail total sales price with taxes",
        digits=(16, 4),
        compute="_compute_retail_total_sale_price_taxes",
        store=True,
    )
    
    
    internal_tax_base = fields.Float(
        string="Internal tax base",
        digits=(16, 4),
        compute="_compute_internal_tax_base",
        store=True,
    )
    internal_aliquot = fields.Float(
        string="Internal aliquot %",
        digits=(16, 4),
    )
    internal_minimum = fields.Float(
        string="Internal minimum",
        digits=(16, 4),
    )
    internal_determined_tax = fields.Float(
        string="Internal determined tax",
        digits=(16, 4),
        compute="_compute_internal_determined_tax",
        store=True,
    )
    
    ad_emergency_tax_base = fields.Float(
        string="Ad. Emergency tax base",
        digits=(16, 4),
        compute="_compute_ad_emergency_tax_base",
        store=True,
    )
    ad_emergency_aliquot = fields.Float(
        string="Ad. Emergency aliquot %",
        digits=(16, 4),
    )
    ad_emergency_determined_tax = fields.Float(
        string="Ad. Emergency determined tax",
        digits=(16, 4),
        compute="_compute_ad_emergency_determined_tax",
        store=True,
    )
    
    
    fet_tax_base = fields.Float(
        string="FET tax base",
        digits=(16, 4),
        compute="_compute_fet_tax_base",
        store=True,
    )
    fet_determined_tax = fields.Float(
        string="FET determined tax",
        digits=(16, 4),
        compute="_compute_fet_determined_tax",
        store=True,
    )
    
    
    iva_tax_base = fields.Float(
        string="IVA tax base",
        digits=(16, 4),
        compute="_compute_iva_tax_base",
        store=True,
    )
    iva_aliquot = fields.Float(
        string="IVA aliquot %",
        digits=(16, 4),
        default=21,
    )
    iva_determined_tax = fields.Float(
        string="IVA determined tax",
        digits=(16, 4),
        compute="_compute_iva_determined_tax",
        store=True,
    )

    #=========================================================================================================================================================

    @api.depends('wholesale_price')
    def _compute_wholesale_net_sale_price(self):
        for rec in self:
            if rec.wholesale_price:
                rec.wholesale_net_sale_price = rec.wholesale_price
            else:
                rec.wholesale_net_sale_price = 0.00
                
    @api.depends('wholesale_price', 'wholesale_net_sale_price')
    def _compute_wholesale_iva(self):
        for rec in self:
            if rec.wholesale_net_sale_price:
                rec.wholesale_iva = rec.wholesale_net_sale_price * 0.21
            else:
                rec.wholesale_iva = 0.00
    
    @api.depends('retail_internal')
    def _compute_wholesale_internal(self):
        for rec in self:
            if rec.retail_internal:
                rec.wholesale_internal = rec.retail_internal
            else:
                rec.wholesale_internal = 0.00
                
    @api.depends('retail_ad_emergency')
    def _compute_wholesale_ad_emergency(self):
        for rec in self:
            if rec.retail_ad_emergency:
                rec.wholesale_ad_emergency = rec.retail_ad_emergency
            else:
                rec.wholesale_ad_emergency = 0.00
    
    @api.depends('retail_fet')
    def _compute_wholesale_fet(self):
        for rec in self:
            if rec.retail_fet:
                rec.wholesale_fet = rec.retail_fet
            else:
                rec.wholesale_fet = 0.00
    
    @api.depends('wholesale_net_sale_price','wholesale_iva','wholesale_internal','wholesale_ad_emergency','wholesale_fet')
    def _compute_wholesale_total_sale_price_taxes(self):
        for rec in self:
            rec.wholesale_total_sale_price_taxes = rec.wholesale_net_sale_price + rec.wholesale_iva + rec.wholesale_internal + rec.wholesale_ad_emergency + rec.wholesale_fet

    #=========================================================================================================================================================

    @api.depends('retail_price')
    def _compute_retail_net_sale_price(self):
        for rec in self:
            if rec.retail_price:
                rec.retail_net_sale_price = rec.retail_price
            else:
                rec.retail_net_sale_price = 0.00
                
    @api.depends('retail_net_sale_price')
    def _compute_retail_iva(self):
        for rec in self:
            if rec.retail_net_sale_price:
                rec.retail_iva = rec.retail_net_sale_price * 0.21
            else:
                rec.retail_iva = 0.00
                
    @api.depends('internal_determined_tax')
    def _compute_retail_internal(self):
        for rec in self:
            if rec.internal_determined_tax:
                rec.retail_internal = rec.internal_determined_tax
            else:
                rec.retail_internal = 0.00
                
    @api.depends('ad_emergency_determined_tax')
    def _compute_retail_ad_emergency(self):
        for rec in self:
            if rec.ad_emergency_determined_tax:
                rec.retail_ad_emergency = rec.ad_emergency_determined_tax
            else:
                rec.retail_ad_emergency = 0.00
                
    @api.depends('fet_determined_tax')
    def _compute_retail_fet(self):
        for rec in self:
            if rec.fet_determined_tax:
                rec.retail_fet = rec.fet_determined_tax
            else:
                rec.retail_fet = 0.00
                
    @api.depends('retail_net_sale_price','retail_iva','retail_internal','retail_ad_emergency','retail_fet')
    def _compute_retail_total_sale_price_taxes(self):
        for rec in self:
            rec.retail_total_sale_price_taxes = rec.retail_net_sale_price + rec.retail_iva + rec.retail_internal + rec.retail_ad_emergency + rec.retail_fet

    #=========================================================================================================================================================

    @api.depends('retail_price')
    def _compute_internal_tax_base(self):
        for rec in self:
            if rec.retail_price:
                rec.internal_tax_base = rec.retail_price
            else:
                rec.internal_tax_base = 0.00
                
    @api.depends('internal_tax_base','internal_aliquot','internal_minimum')
    def _compute_internal_determined_tax(self):
        for rec in self:
            if rec.internal_tax_base and rec.internal_aliquot and rec.internal_minimum:
                tax = (rec.internal_tax_base * rec.internal_aliquot) / 100
                if tax < rec.internal_minimum:
                    rec.internal_determined_tax = rec.internal_minimum
                else:
                    rec.internal_determined_tax = tax
            else:
                rec.internal_determined_tax = 0.00
            if rec.amount_type == 'internal_taxes':
                rec.amount = rec.internal_determined_tax

    #=========================================================================================================================================================
                
    @api.depends('sale_price_afip')
    def _compute_ad_emergency_tax_base(self):
        for rec in self:
            if rec.sale_price_afip:
                rec.ad_emergency_tax_base = rec.sale_price_afip
            else:
                rec.ad_emergency_tax_base = 0.00
                
    @api.depends('ad_emergency_aliquot','ad_emergency_tax_base')
    def _compute_ad_emergency_determined_tax(self):
        for rec in self:
            if rec.ad_emergency_tax_base and rec.ad_emergency_aliquot:
                rec.ad_emergency_determined_tax = (rec.ad_emergency_tax_base * rec.ad_emergency_aliquot) / 100
            else:
                rec.ad_emergency_determined_tax = 0.00
            if rec.amount_type == 'ad_emergency':
                rec.amount = rec.ad_emergency_determined_tax

    #=========================================================================================================================================================

    @api.depends('sale_price_afip','retail_ad_emergency','retail_iva')
    def _compute_fet_tax_base(self):
        for rec in self:
            if rec.sale_price_afip and rec.retail_ad_emergency and rec.retail_iva:
                rec.fet_tax_base = rec.sale_price_afip - rec.retail_iva - rec.retail_ad_emergency
            else:
                rec.fet_tax_base = 0.00

    @api.depends('fet_tax_base','fixed_fet')
    def _compute_fet_determined_tax(self):
        for rec in self:
            if rec.fet_tax_base and rec.fixed_fet:
                rec.fet_determined_tax = ((rec.fet_tax_base * 7) / 100) + ((rec.fet_tax_base * 0.35) / 100) + rec.fixed_fet
            else:
                rec.fet_determined_tax = 0.00
            if rec.amount_type == 'fet':
                rec.amount = rec.fet_determined_tax

    #=========================================================================================================================================================

    @api.depends('retail_net_sale_price')
    def _compute_iva_tax_base(self):
        for rec in self:
            if rec.retail_net_sale_price:
                rec.iva_tax_base = rec.retail_net_sale_price
            else:
                rec.iva_tax_base = 0.00

    @api.depends('iva_aliquot','iva_tax_base')
    def _compute_iva_determined_tax(self):
        for rec in self:
            if rec.iva_tax_base and rec.iva_aliquot:
                rec.iva_determined_tax = (rec.iva_tax_base * rec.iva_aliquot) / 100
            else:
                rec.iva_determined_tax = 0.00

    #=========================================================================================================================================================
    
    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        self.ensure_one()
        if self.amount_type == 'fet':
            return quantity * self.fet_determined_tax
        if self.amount_type == 'ad_emergency':
            return quantity * self.ad_emergency_determined_tax
        if self.amount_type == 'internal_taxes':
            return quantity * self.internal_determined_tax
        return super(AccountTax, self)._compute_amount(base_amount, price_unit, quantity, product, partner)

