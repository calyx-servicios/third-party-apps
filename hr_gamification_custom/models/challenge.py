# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Challenge(models.Model):

    _inherit = 'gamification.challenge'

    total_scoring = fields.Float(string="Scoring")
    name_tag_ids = fields.Many2many(
        comodel_name="gamification.tag",
        string="Tags",
    )

    @api.onchange('line_ids')
    def on_change_line_ids(self):
        self.total_scoring = 0
        for lines in self.line_ids:
            self.total_scoring += lines.scoring


class ChallengeLine(models.Model):

    _inherit = 'gamification.challenge.line'

    scoring = fields.Float(string="Scoring", related="definition_id.scoring")


