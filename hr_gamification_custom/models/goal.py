from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, ValidationError

class GoalDefinition(models.Model):

    _inherit = 'gamification.goal.definition'

    scoring = fields.Percent(string="Scoring")
    scoring_rules = fields.One2many('scoring.rule','rule_id')
    
    @api.constrains('scoring_rules')
    def _check_scoring_rules(self):
        for rule in self.scoring_rules:
            if rule.interval_from > rule.interval_to:
                raise UserError("Invalid Range")

class Goal(models.Model):

    _name = 'gamification.goal'
    _inherit = 'mail.thread','gamification.goal'

    state = fields.Selection([
        ('draft', "Draft"),
        ('inprogress', "In progress"),
        ('reached', "Reached"),
        ('failed', "Failed"),
        ('approved', "Approved"),
        ('declined', "Declined"),
        ('canceled', "Canceled"),
    ], default='draft', string='State', required=True, track_visibility='always')
    total_scoring = fields.Percent(string="Total Scoring", related="definition_id.scoring", store=True)
    current_scoring = fields.Percent(string="Current Scoring")
    current = fields.Float("Current Value", required=True, default=0, track_visibility='always')

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_decline(self):
        for rec in self:
            rec.state = 'declined'

    def action_undo(self):
        for rec in self:
            rec.state = 'draft'

    @api.onchange('current')
    def _onchange_current(self):
        if self.definition_id.scoring_rules:
            for rule in self.definition_id.scoring_rules:
                if rule.interval_from <= self.current <= rule.interval_to:
                    self.current_scoring = self.definition_id.scoring * rule.scoring_goal / 100
                    break

class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')),
                                               ('res_id', '=', vals.get('res_id')),
                                               ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.unlink()
        res = super(Followers, self).create(vals)
        return res