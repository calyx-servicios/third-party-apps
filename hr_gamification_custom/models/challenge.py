from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta, MO
from odoo.exceptions import Warning

def start_end_date_for_period(period, default_start_date=False, default_end_date=False):
    today = date.today()
    if period == 'daily':
        start_date = today
        end_date = start_date
    elif period == 'weekly':
        start_date = today + relativedelta(weekday=MO(-1))
        end_date = start_date + timedelta(days=7)
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today + relativedelta(months=1, day=1, days=-1)
    elif period == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else: 
        start_date = default_start_date  
        end_date = default_end_date

        return (start_date, end_date)

    return fields.Datetime.to_string(start_date), fields.Datetime.to_string(end_date)

class Challenge(models.Model):

    _inherit = 'gamification.challenge'

    total_scoring = fields.Percent(string="Scoring")
    name_tag_ids = fields.Many2many(
        comodel_name="gamification.tag",
        string="Tags",
    )
    tag_id = fields.Many2one(comodel_name="gamification.tag", compute='_compute_tag_id', store=True, string="Tag") 
    
    @api.onchange('manager_id')
    def onchange_manager_id(self):
        users = self.env.ref('hr_gamification_custom.group_objectives_approver').users.ids
        return {'domain': {'manager_id': [('id', 'in', users)]}}

    @api.depends('name_tag_ids')
    def _compute_tag_id(self):
        for record in self:
            record.tag_id = record.name_tag_ids

    @api.onchange('line_ids')
    def on_change_line_ids(self):
        self.total_scoring = 0
        for lines in self.line_ids:
            self.total_scoring += lines.scoring

    def _generate_goals_from_challenge(self):
        Goals = self.env['gamification.goal']
        for challenge in self:
            (start_date, end_date) = start_end_date_for_period(
                challenge.period, challenge.start_date, challenge.end_date)
            to_update = Goals.browse(())
            for line in challenge.line_ids:
                date_clause = ""
                query_params = [line.id]
                if start_date:
                    date_clause += " AND g.start_date = %s"
                    query_params.append(start_date)
                if end_date:
                    date_clause += " AND g.end_date = %s"
                    query_params.append(end_date)
                query = """SELECT u.id AS user_id
                             FROM res_users u
                        LEFT JOIN gamification_goal g
                               ON (u.id = g.user_id)
                            WHERE line_id = %s
                              {date_clause}
                        """.format(date_clause=date_clause)
                self.env.cr.execute(query, query_params)
                user_with_goal_ids = {it for [it] in self.env.cr._obj}
                participant_user_ids = set(challenge.user_ids.ids)
                user_squating_challenge_ids = user_with_goal_ids - participant_user_ids
                if user_squating_challenge_ids:
                    # users that used to match the challenge
                    Goals.search([
                        ('challenge_id', '=', challenge.id),
                        ('user_id', 'in', list(user_squating_challenge_ids))
                    ]).unlink()
                values = {
                    'definition_id': line.definition_id.id,
                    'line_id': line.id,
                    'target_goal': line.target_goal,
                    'state': 'inprogress',
                    'tag_id': self.tag_id.id,
                }
                if start_date:
                    values['start_date'] = start_date
                if end_date:
                    values['end_date'] = end_date
                if challenge.remind_update_delay:
                    values['remind_update_delay'] = challenge.remind_update_delay
                for user_id in (participant_user_ids - user_with_goal_ids):
                    values['user_id'] = user_id
                    to_update |= Goals.create(values)
            to_update.update_goal()
        return True

    @api.multi
    def action_check(self):
        self.env['gamification.goal'].search([
            ('challenge_id', 'in', self.ids),
            ('state', '=', 'inprogress')
        ]).unlink()
        goal=[]
        total_scoring = 0
        today = date.today()
        for user in self.user_ids:
            if self.start_date and self.end_date:
                goal = self.env['gamification.goal'].search([
                ('user_id', '=', user.id),('state', '!=', "draft"),'|','|',
                '&',('start_date','<=',self.start_date),('end_date','>=',self.start_date),
                '&',('start_date','<=',self.end_date),('end_date','>=',self.end_date),
                '&','&',('start_date','>=',self.start_date),('start_date','<=',self.end_date),
                '&',('end_date','>=',self.start_date),('end_date','<=',self.end_date)
                ])
            else:
                if self.start_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft"),'|',
                    '&',('start_date','<=',self.start_date),('end_date','>=',self.start_date),
                    ('end_date','>=',self.start_date)
                    ])
                if self.end_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft"),'|','|',
                    '&',('start_date','<=',today),('end_date','>=',today),
                    '&',('start_date','<=',self.end_date),('end_date','>=',self.end_date),
                    '&','&',('start_date','>=',today),('start_date','<=',self.end_date),
                    '&',('end_date','>=',today),('end_date','<=',self.end_date)
                    ])
                if not self.start_date and not self.end_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft")
                    ])
            for scorings in goal:
                total_scoring += scorings.total_scoring 
            if total_scoring + self.total_scoring > 100 :
                raise Warning(_("user cant have a total scoring over 100%"))
            total_scoring = 0
        return self._update_all()


    @api.multi
    def action_start(self):
        goal=[]
        total_scoring = 0
        today = date.today()
        for user in self.user_ids:
            if self.start_date and self.end_date:
                goal = self.env['gamification.goal'].search([
                ('user_id', '=', user.id),('state', '!=', "draft"),'|','|',
                '&',('start_date','<=',self.start_date),('end_date','>=',self.start_date),
                '&',('start_date','<=',self.end_date),('end_date','>=',self.end_date),
                '&','&',('start_date','>=',self.start_date),('start_date','<=',self.end_date),
                '&',('end_date','>=',self.start_date),('end_date','<=',self.end_date)
                ])
            else:
                if self.start_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft"),'|',
                    '&',('start_date','<=',self.start_date),('end_date','>=',self.start_date),
                    ('end_date','>=',self.start_date)
                    ])
                if self.end_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft"),'|','|',
                    '&',('start_date','<=',today),('end_date','>=',today),
                    '&',('start_date','<=',self.end_date),('end_date','>=',self.end_date),
                    '&','&',('start_date','>=',today),('start_date','<=',self.end_date),
                    '&',('end_date','>=',today),('end_date','<=',self.end_date)
                    ])
                if not self.start_date and not self.end_date:
                    goal = self.env['gamification.goal'].search([
                    ('user_id', '=', user.id),('state', '!=', "draft")
                    ])
            for scorings in goal:
                total_scoring += scorings.total_scoring 
            if total_scoring + self.total_scoring > 100 :
                raise Warning(_("user cant have a total scoring over 100%"))
            total_scoring = 0
        return self.write({'state': 'inprogress'})

class ChallengeLine(models.Model):

    _inherit = 'gamification.challenge.line'

    scoring = fields.Percent(string="Scoring", related="definition_id.scoring")


