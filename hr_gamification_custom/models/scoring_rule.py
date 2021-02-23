from odoo import api, fields, models, _, exceptions

class ScoringRules(models.Model):
    _name = 'scoring.rule'
    _description = 'Rule for scoring'

    rule_id = fields.Many2one('gamification.goal.definition', string='Rule')
    interval_from = fields.Integer(string="From")
    interval_to = fields.Integer(string="To")
    scoring_goal = fields.Float(string="scoring goal")
    
