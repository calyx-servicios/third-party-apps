from odoo import fields, models, _
from odoo.exceptions import Warning


class GamificationTag(models.Model):
    _name = "gamification.tag"
    _rec_name = "tag_name"
    _order = "sequence"

    tag_name = fields.Char("Tag Name")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    def unlink(self):
        challenge_obj = self.env["gamification.challenge"]
        rule_ranges = challenge_obj.search([("tag_name", "=", self.id)])
        if rule_ranges:
            raise Warning(
                _(
                    "You are trying to delete a record "
                    "that is still referenced in one o more challenges, "
                    "try to archive it."
                )
            )
        return super(GamificationTag, self).unlink()
