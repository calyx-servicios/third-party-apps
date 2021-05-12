from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, ValidationError

class MinimunObjectiveControl(models.TransientModel):
    _name = 'minimun.objective.control'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')

    def check_objective_minimun(self):
        goal=[]
        users=[]
        incomplete_users=""
        total_scoring = 0
        users = self.env['res.users'].search([('id','>',1)])
        for user in users:
            goal = self.env['gamification.goal'].search([
                ('user_id', '=', user.id),('state', '!=', "draft"),'|','|',
                '&',('start_date','<=',self.date_from),('end_date','>=',self.date_from),
                '&',('start_date','<=',self.date_to),('end_date','>=',self.date_to),
                '&','&',('start_date','>=',self.date_from),('start_date','<=',self.date_to),
                '&',('end_date','>=',self.date_from),('end_date','<=',self.date_to)
                ])
            for scorings in goal:
                total_scoring += scorings.total_scoring 
            if total_scoring < 100 and user.has_group('hr_gamification_custom.group_objectives_manager'):
                incomplete_users += "\n" + user.name
            total_scoring = 0
        if incomplete_users:
            raise ValidationError(_("the following users doesnt have 100 scoring %s")% incomplete_users)