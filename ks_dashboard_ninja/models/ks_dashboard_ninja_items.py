# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json


class KsDashboardNinjaItems(models.Model):
    _name = 'ks_dashboard_ninja.item'

    name = fields.Char(string="Name", size=256)
    ks_model_id = fields.Many2one('ir.model', string='Model', required=True,
                                  domain="[('access_ids','!=',False),('transient','=',False),('model','not ilike','base_import%'),('model','not ilike','ir.%'),('model','not ilike','web_editor.%'),('model','not ilike','web_tour.%'),('model','!=','mail.thread'),('model','!=','ks_dashboard_ninja.item'),('model','!=','ks_dashboard_ninja.board'),('model','!=','ks_dashboard_ninja.board_template')]")
    ks_domain = fields.Char(string="Domain")

    ks_domain_temp = fields.Char(string="Domain Substitute")
    ks_background_color = fields.Char(default="#337ab7,0.99", string="Background Color")
    ks_icon = fields.Binary(string="Icon", attachment=True)
    ks_default_icon = fields.Char(string="Icon", default="bar-chart")
    ks_default_icon_color = fields.Char(default="#ffffff,0.99", string="Icon Color")
    ks_icon_select = fields.Char(string="Icon Option", default="Default")
    ks_font_color = fields.Char(default="#ffffff,0.99", string="Font Color")
    ks_dashboard_item_theme = fields.Char(default="blue", string="Theme")
    ks_layout = fields.Selection([('layout1', 'Layout 1'),
                                  ('layout2', 'Layout 2'),
                                  ('layout3', 'Layout 3'),
                                  ('layout4', 'Layout 4'),
                                  ('layout5', 'Layout 5'),
                                  ('layout6', 'Layout 6'),
                                  ], default=('layout1'), required=True, string="Layout")
    ks_preview = fields.Integer(default=1, string="Preview")
    ks_model_name = fields.Char(related='ks_model_id.model', readonly=True)

    ks_record_count_type = fields.Selection([('count', 'Count'),
                                             ('sum', 'Sum'),
                                             ('average', 'Average')], string="Record Count Type", default="count")
    ks_record_count = fields.Float(string="Record Count", compute='ks_get_record_count', readonly=True)
    ks_record_field = fields.Many2one('ir.model.fields',
                                      domain="[('model_id','=',ks_model_id),('name','!=','id'),'|','|',('ttype','=','integer'),('ttype','=','float'),('ttype','=','monetary')]",
                                      string="Record Field")

    # Date Filter Fields
    # Condition to tell if date filter is applied or not
    ks_isDateFilterApplied = fields.Boolean(default=False)
    # This field will store on which field the date filter will be applied
    ks_date_filter_field = fields.Many2one('ir.model.fields',
                                           domain="[('model_id','=',ks_model_id),'|',('ttype','=','date'),('ttype','=','datetime')]",
                                           string="Date Filter Field")



    # Pro Fields
    ks_dashboard_ninja_board_id = fields.Many2one('ks_dashboard_ninja.board',
                                                  default=lambda self: self._context[
                                                      'ks_dashboard_id'] if 'ks_dashboard_id' in self._context else False)

    # Chart related fields
    ks_dashboard_item_type = fields.Selection([('ks_tile', 'Tile'),
                                               ('ks_bar_chart', 'Bar Chart'),
                                               ('ks_horizontalBar_chart', 'Horizontal Bar Chart'),
                                               ('ks_line_chart', 'Line Chart'),
                                               ('ks_area_chart', 'Area Chart'),
                                               ('ks_pie_chart', 'Pie Chart'),
                                               ('ks_doughnut_chart', 'Doughnut Chart'),
                                               ('ks_polarArea_chart', 'Polar Area Chart'),
                                               ('ks_list_view', 'List View'),
                                               ], default=lambda self: self._context.get('ks_dashboard_item_type','ks_tile'), required=True, string="Dashboard Item Type")
    ks_chart_groupby_type = fields.Char(compute='get_chart_groupby_type')
    ks_chart_relation_groupby = fields.Many2one('ir.model.fields',
                                                domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True),'|',"
                                                       "'|',('ttype','=','many2one'),('ttype','=','date'),('ttype','=','datetime')]",
                                                string="Group By")

    ks_chart_date_groupby = fields.Selection([('day', 'Day'),
                                              ('week', 'Week'),
                                              ('month', 'Month'),
                                              ('quarter', 'Quarter'),
                                              ('year', 'Year'),
                                              ], string="Dashboard Item Chart Group By Type")
    ks_graph_preview = fields.Char(string="Preview", default="Graph Preview")
    ks_chart_data = fields.Char(string="Chart Data in string form", compute='ks_get_chart_data')
    ks_chart_data_count_type = fields.Selection([('count', 'Count'), ('sum', 'Sum'), ('average', 'Average')],
                                                string="Chart Data Count Type", default="sum")
    ks_chart_measure_field = fields.Many2many('ir.model.fields', 'ks_dn_measure_field_rel', 'measure_field_id',
                                              'field_id',
                                              domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True),'|','|',"
                                                     "('ttype','=','integer'),('ttype','=','float'),"
                                                     "('ttype','=','monetary')]",
                                              string="Record Field")
    ks_chart_measure_field_2 = fields.Many2many('ir.model.fields', 'ks_dn_measure_field_rel_2', 'measure_field_id_2',
                                                'field_id',
                                                domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True),'|','|',"
                                                       "('ttype','=','integer'),('ttype','=','float'),"
                                                       "('ttype','=','monetary')]",
                                                string="Line Measure")

    ks_bar_chart_stacked = fields.Boolean(string="Stacked Bar Chart")

    ks_sort_by_field = fields.Many2one('ir.model.fields',
                                       domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True),"
                                              "('ttype','!=','one2many'),('ttype','!=','many2one'),('ttype','!=','binary')]",
                                       string="Sort By Field")
    ks_sort_by_order = fields.Selection([('ASC', 'Ascending'), ('DESC', 'Descending')],
                                        string="Sort Order")
    ks_record_data_limit = fields.Integer(string="Record Limit")

    # For next feature build.
    # ks_graph_size = fields.Selection([('Half (1/2)', 'half'), ('Quarter n Half (3/4)', 'q_n_half'), ('Full ', 'full')],
    #                                  string="Sorting Order")

    ks_list_view_preview = fields.Char(string="List View Preview", default="List View Preview")

    ks_chart_item_color = fields.Selection(
        [('default', 'Default'), ('cool', 'Cool'), ('warm', 'Warm'), ('neon', 'Neon')],
        string="Chart Color Palette", default="default")

    # ------------------------ List View Fields ------------------------------

    ks_list_view_type = fields.Selection([('ungrouped', 'Un-Grouped'), ('grouped', 'Grouped')], default="ungrouped",
                                         string="List View Type", required=True)
    ks_list_view_fields = fields.Many2many('ir.model.fields', 'ks_dn_list_field_rel', 'list_field_id', 'field_id',
                                           domain="[('model_id','=',ks_model_id),('store','=',True),"
                                                  "('ttype','!=','one2many'),('ttype','!=','many2many'),('ttype','!=','binary')]",
                                           string="Fields to show in list")

    ks_list_view_group_fields = fields.Many2many('ir.model.fields', 'ks_dn_list_group_field_rel', 'list_field_id',
                                                 'field_id',
                                                 domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True),'|','|',"
                                                        "('ttype','=','integer'),('ttype','=','float'),"
                                                        "('ttype','=','monetary')]",
                                                 string="List View Grouped Fields")
    ks_list_view_data = fields.Char(string="List View Data in JSon", compute='ks_get_list_view_data')

    # -------------------- Multi Company Feature ---------------------
    ks_company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)



    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if not name:
                name = rec.ks_model_id.name
            res.append((rec.id, name))

        return res

    @api.onchange('ks_layout')
    def layout_four_font_change(self):
        if self.ks_layout == 'layout4':
            self.ks_font_color = self.ks_background_color
            self.ks_default_icon_color = "#ffffff,0.99"
        elif self.ks_layout == 'layout6':
            self.ks_font_color = "#ffffff,0.99"
            self.ks_default_icon_color = self.ks_get_dark_color(self.ks_background_color.split(',')[0],
                                                                self.ks_background_color.split(',')[1])
        else:
            self.ks_default_icon_color = "#ffffff,0.99"
            self.ks_font_color = "#ffffff,0.99"

    # To convert color into 10% darker. Percentage amount is hardcoded. Change amt if want to change percentage.
    def ks_get_dark_color(self, color, opacity):
        num = int(color[1:], 16)
        amt = -25
        R = (num >> 16) + amt
        R = (255 if R > 255 else 0 if R < 0 else R) * 0x10000
        G = (num >> 8 & 0x00FF) + amt
        G = (255 if G > 255 else 0 if G < 0 else G) * 0x100
        B = (num & 0x0000FF) + amt
        B = (255 if B > 255 else 0 if B < 0 else B)
        return "#" + hex(0x1000000 + R + G + B).split('x')[1][1:] + "," + opacity

    @api.onchange('ks_model_id')
    def make_record_field_empty(self):
        for rec in self:
            rec.ks_record_field = False
            rec.ks_domain = False
            # To show "created on" by default on date filter field on model select.
            if rec.ks_model_id:
                is_create_field  = False
                datetime_field_list = rec.ks_date_filter_field.search(
                    [('model_id', '=', rec.ks_model_id.id), '|', ('ttype', '=', 'date'),
                     ('ttype', '=', 'datetime')]).read(['id', 'name'])
                for field in datetime_field_list:
                    if field['name'] == 'create_date':
                        rec.ks_date_filter_field = field['id']
                        is_create_field = True
                if not is_create_field:
                    rec.ks_date_filter_field = False
            else:
                rec.ks_date_filter_field = False
            # Pro
            rec.ks_record_field = False
            rec.ks_chart_measure_field = False
            rec.ks_chart_measure_field_2 =  False
            rec.ks_chart_relation_groupby = False
            rec.ks_chart_date_groupby = False
            rec.ks_sort_by_field = False
            rec.ks_sort_by_order = False
            rec.ks_record_data_limit = False
            rec.ks_list_view_fields = False

    @api.onchange('ks_record_count', 'ks_layout', 'name', 'ks_model_id', 'ks_domain', 'ks_icon_select',
                  'ks_default_icon', 'ks_icon',
                  'ks_background_color', 'ks_font_color', 'ks_default_icon_color')
    def ks_preview_update(self):
        self.ks_preview += 1

    @api.onchange('ks_dashboard_item_theme')
    def change_dashboard_item_theme(self):
        if self.ks_dashboard_item_theme == "red":
            self.ks_background_color = "#d9534f,0.99"
            self.ks_default_icon_color = "#ffffff,0.99"
            self.ks_font_color = "#ffffff,0.99"
        elif self.ks_dashboard_item_theme == "blue":
            self.ks_background_color = "#337ab7,0.99"
            self.ks_default_icon_color = "#ffffff,0.99"
            self.ks_font_color = "#ffffff,0.99"
        elif self.ks_dashboard_item_theme == "yellow":
            self.ks_background_color = "#f0ad4e,0.99"
            self.ks_default_icon_color = "#ffffff,0.99"
            self.ks_font_color = "#ffffff,0.99"
        elif self.ks_dashboard_item_theme == "green":
            self.ks_background_color = "#5cb85c,0.99"
            self.ks_default_icon_color = "#ffffff,0.99"
            self.ks_font_color = "#ffffff,0.99"

        if self.ks_layout == 'layout4':
            self.ks_font_color = self.ks_background_color

        elif self.ks_layout == 'layout6':
            self.ks_default_icon_color = self.ks_get_dark_color(self.ks_background_color.split(',')[0],
                                                                self.ks_background_color.split(',')[1])

    @api.multi
    @api.depends('ks_record_count_type', 'ks_model_id', 'ks_domain', 'ks_record_field')
    def ks_get_record_count(self):
        for rec in self:
            if rec.ks_record_count_type == 'count':
                rec.ks_record_count = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'search_count', rec)
            elif rec.ks_record_count_type == 'sum' and rec.ks_record_field:
                ks_records = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'search', rec)
                for filtered_records in ks_records:
                    rec.ks_record_count += filtered_records[rec.ks_record_field.name]
            elif rec.ks_record_count_type == 'average' and rec.ks_record_field:
                ks_records = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'search', rec)
                ks_record_count = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'search_count', rec)
                for filtered_records in ks_records:
                    rec.ks_record_count += filtered_records[rec.ks_record_field.name]
                rec.ks_record_count = rec.ks_record_count / ks_record_count if ks_record_count else 0
            else:
                rec.ks_record_count = 0

    # Writing separate function to fetch dashboard item data
    def ks_fetch_model_data(self, ks_model_name, ks_domain, ks_func, rec):
        data = 0
        try:
            if ks_domain and ks_domain != '[]' and ks_model_name:
                proper_domain = self.ks_convert_into_proper_domain(ks_domain, rec)
                if ks_func == 'search_count':
                    data = self.env[ks_model_name].search_count(proper_domain)
                elif ks_func == 'search':
                    data = self.env[ks_model_name].search(proper_domain)
            elif ks_model_name:
                # Have to put extra if condition here because on load,model giving False value
                proper_domain = self.ks_convert_into_proper_domain(False, rec)
                if ks_func == 'search_count':
                    data = self.env[ks_model_name].search_count(proper_domain)

                elif ks_func == 'search':
                    data = self.env[ks_model_name].search(proper_domain)
            else:
                return 0
        except Exception as e:
            return 0
        return data

    def ks_convert_into_proper_domain(self, ks_domain, rec):
        if ks_domain and "%UID" in ks_domain:
            ks_domain = ks_domain.replace('"%UID"', str(self.env.user.id))
        selected_start_date = rec.env["ks_dashboard_ninja.board"].browse(
            rec.ks_dashboard_ninja_board_id.id).ks_dashboard_start_date
        selected_end_date = rec.env["ks_dashboard_ninja.board"].browse(
            rec.ks_dashboard_ninja_board_id.id).ks_dashboard_end_date
        if ks_domain:
            # try:
            proper_domain = eval(ks_domain)
            if selected_start_date and selected_end_date and rec.ks_date_filter_field:
                proper_domain.extend([(rec.ks_date_filter_field.name, ">=", selected_start_date),
                                      (rec.ks_date_filter_field.name, "<=", selected_end_date)])
                rec.ks_isDateFilterApplied = True
            else:
                rec.ks_isDateFilterApplied = False
        else:
            if selected_end_date and selected_end_date and rec.ks_date_filter_field:
                proper_domain = [(rec.ks_date_filter_field.name, ">=", selected_start_date),
                                 (rec.ks_date_filter_field.name, "<=", selected_end_date)]
            else:
                proper_domain = []
        return proper_domain


# Pro Function

    @api.multi
    @api.onchange('ks_chart_relation_groupby')
    def get_chart_groupby_type(self):
        for rec in self:
            if rec.ks_chart_relation_groupby.ttype == 'datetime' or rec.ks_chart_relation_groupby.ttype == 'date':
                rec.ks_chart_groupby_type = 'date_type'
            elif rec.ks_chart_relation_groupby.ttype == 'many2one':
                rec.ks_chart_groupby_type = 'relational_type'
                rec.ks_chart_date_groupby = False
            else:
                rec.ks_chart_groupby_type = 'none'
                rec.ks_chart_date_groupby = False

    # Using this function just to let js call rpc to load some data later
    @api.model
    def ks_chart_load(self):
        return True


    @api.multi
    @api.depends('ks_chart_measure_field', 'ks_chart_relation_groupby', 'ks_chart_date_groupby', 'ks_domain',
                 'ks_dashboard_item_type', 'ks_model_id', 'ks_sort_by_field', 'ks_sort_by_order',
                 'ks_chart_measure_field_2','ks_record_data_limit', 'ks_chart_data_count_type')
    def ks_get_chart_data(self):
        for rec in self:
            if rec.ks_dashboard_item_type and rec.ks_dashboard_item_type != 'ks_tile' and rec.ks_model_id and rec.ks_chart_data_count_type:
                ks_chart_data = {'labels': [], 'datasets': []}

                ks_chart_measure_field = []
                ks_chart_measure_field_2 = []
                if rec.ks_chart_data_count_type=="count":
                    ks_chart_data['datasets'].append({'data': [], 'label': "Count"})
                else:
                    if rec.ks_dashboard_item_type == 'ks_bar_chart':
                        for res in rec.ks_chart_measure_field_2:
                            ks_chart_measure_field_2.append(res.name)
                            ks_chart_data['datasets'].append(
                                {'data': [], 'label': res.field_description, 'type': 'line'})
                    for res in rec.ks_chart_measure_field:
                        ks_chart_measure_field.append(res.name)
                        ks_chart_data['datasets'].append({'data': [], 'label': res.field_description})

                # ks_chart_measure_field = [res.name for res in rec.ks_chart_measure_field]
                ks_chart_groupby_relation_field = rec.ks_chart_relation_groupby.name

                ks_chart_domain = self.ks_convert_into_proper_domain(rec.ks_domain, rec)
                orderby = rec.ks_sort_by_field.name if rec.ks_sort_by_field else "id"
                if rec.ks_sort_by_order:
                    orderby = orderby + " " + rec.ks_sort_by_order
                limit = rec.ks_record_data_limit if rec.ks_record_data_limit else False
                if (rec.ks_chart_data_count_type != "count" and ks_chart_measure_field) or (
                        rec.ks_chart_data_count_type == "count" and not ks_chart_measure_field):
                    if rec.ks_chart_groupby_type == 'relational_type' and rec.ks_chart_relation_groupby:
                        ks_chart_data['groupByIds'] = []
                        ks_chart_records = self.env[rec.ks_model_name].read_group(ks_chart_domain,
                                                                                  ks_chart_measure_field + ks_chart_measure_field_2 + [
                                                                                      ks_chart_groupby_relation_field],
                                                                                  [ks_chart_groupby_relation_field],
                                                                                  orderby=orderby, limit=limit)

                        for res in ks_chart_records:
                            if res[ks_chart_groupby_relation_field] and all(
                                    measure_field in res for measure_field in ks_chart_measure_field):
                                ks_chart_data['labels'].append(res[ks_chart_groupby_relation_field][1])
                                ks_chart_data['groupByIds'].append(res[ks_chart_groupby_relation_field][0])
                                counter = 0
                                if ks_chart_measure_field:
                                    if ks_chart_measure_field_2:
                                        for field_rec in ks_chart_measure_field_2:
                                            data = res[field_rec] if rec.ks_chart_data_count_type == 'sum' else res[
                                                                                                                    field_rec] / \
                                                                                                                res[
                                                                                                                    ks_chart_groupby_relation_field + "_count"]
                                            ks_chart_data['datasets'][counter]['data'].append(data)
                                            counter += 1
                                    for field_rec in ks_chart_measure_field:
                                        data = res[field_rec] if rec.ks_chart_data_count_type == 'sum' else res[
                                                                                                                field_rec] / \
                                                                                                            res[
                                                                                                                ks_chart_groupby_relation_field + "_count"]
                                        ks_chart_data['datasets'][counter]['data'].append(data)
                                        counter += 1
                                else:
                                    data = res[ks_chart_groupby_relation_field + "_count"]
                                    ks_chart_data['datasets'][0]['data'].append(data)

                    elif rec.ks_chart_groupby_type == 'date_type' and rec.ks_chart_date_groupby :
                        ks_chart_records = self.env[rec.ks_model_name].read_group(ks_chart_domain,
                                                                                  ks_chart_measure_field +
                                                                                  ks_chart_measure_field_2 +[
                                                                                      ks_chart_groupby_relation_field],
                                                                                  [
                                                                                      ks_chart_groupby_relation_field + ":" + rec.ks_chart_date_groupby],
                                                                                  orderby=orderby, limit=limit)
                        # Converting in chart data format
                        # chart_data = {labels:[], datasets:[{}]}
                        for res in ks_chart_records:
                            if res[ks_chart_groupby_relation_field + ":" + rec.ks_chart_date_groupby] and all(
                                    measure_field in res for measure_field in ks_chart_measure_field):
                                ks_chart_data['labels'].append(
                                    res[ks_chart_groupby_relation_field + ":" + rec.ks_chart_date_groupby])
                                counter = 0
                                if ks_chart_measure_field and len(ks_chart_measure_field) != 0:
                                    if ks_chart_measure_field_2:
                                        for field_rec in ks_chart_measure_field_2:
                                            data = res[
                                                field_rec] if rec.ks_chart_data_count_type == 'sum' else res[
                                                                                                             field_rec] / \
                                                                                                         res[
                                                                                                             ks_chart_groupby_relation_field + "_count"]
                                            ks_chart_data['datasets'][counter]['data'].append(data)
                                            counter += 1
                                    for field_rec in ks_chart_measure_field:
                                        data = res[
                                            field_rec] if rec.ks_chart_data_count_type == 'sum' else res[field_rec] / \
                                                                                                     res[
                                                                                                         ks_chart_groupby_relation_field + "_count"]
                                        ks_chart_data['datasets'][counter]['data'].append(data)
                                        counter += 1
                                else:
                                    data = res[ks_chart_groupby_relation_field + "_count"]
                                    ks_chart_data['datasets'][0]['data'].append(data)

                rec.ks_chart_data = json.dumps(ks_chart_data)

    @api.multi
    @api.depends('ks_domain', 'ks_dashboard_item_type', 'ks_model_id', 'ks_sort_by_field', 'ks_sort_by_order',
                 'ks_record_data_limit', 'ks_list_view_fields', 'ks_list_view_group_fields', 'ks_list_view_type', 'ks_chart_relation_groupby',)
    def ks_get_list_view_data(self):
        for rec in self:
            if rec.ks_dashboard_item_type and rec.ks_dashboard_item_type == 'ks_list_view' and rec.ks_model_id:
                ks_list_view_data = {'label': [],
                                     'data_rows': [], 'model': rec.ks_model_name}
                ks_list_view_fields = [res.name for res in rec.ks_list_view_fields]
                ks_list_view_type = [res.ttype for res in rec.ks_list_view_fields]
                ks_chart_domain = self.ks_convert_into_proper_domain(rec.ks_domain, rec)
                orderby = rec.ks_sort_by_field.name if rec.ks_sort_by_field else "id"
                if rec.ks_sort_by_order:
                    orderby = orderby + " " + rec.ks_sort_by_order
                limit = rec.ks_record_data_limit if rec.ks_record_data_limit else False
                if rec.ks_list_view_type == "ungrouped" and rec.ks_list_view_fields:
                    ks_list_view_data['list_view_type'] = 'none'
                    ks_list_view_data['groupby'] = False
                    ks_list_view_data['label'] = [res.field_description for res in rec.ks_list_view_fields]
                    ks_list_view_fields = [res.name for res in rec.ks_list_view_fields]
                    ks_list_view_field_type = [res.ttype for res in rec.ks_list_view_fields]
                    ks_list_view_records = self.env[rec.ks_model_name].sudo().search_read(ks_chart_domain,
                                                                                          ks_list_view_fields,
                                                                                          order=orderby, limit=limit)

                    for res in ks_list_view_records:
                        counter = 0
                        data_row = {'id': res['id'], 'data': []}
                        for field_rec in ks_list_view_fields:
                            if type(res[field_rec]) == fields.datetime or type(res[field_rec]) == fields.date:
                                res[field_rec] = res[field_rec].strftime("%D")

                            elif ks_list_view_type[counter]=="many2one":
                                if res[field_rec]:
                                    res[field_rec] = res[field_rec][1]

                            data_row['data'].append(res[field_rec])
                            counter += 1
                        ks_list_view_data['data_rows'].append(data_row)

                elif rec.ks_list_view_type == "grouped" and rec.ks_list_view_group_fields and rec.ks_chart_relation_groupby:
                    ks_list_fields = []

                    if rec.ks_chart_groupby_type == 'relational_type':
                        ks_list_view_data['list_view_type'] = 'relational_type'
                        ks_list_view_data['groupby'] = rec.ks_chart_relation_groupby.name
                        ks_list_fields.append(rec.ks_chart_relation_groupby.name)
                        ks_list_view_data['label'].append(rec.ks_chart_relation_groupby.field_description)
                        for res in rec.ks_list_view_group_fields:
                            ks_list_fields.append(res.name)
                            ks_list_view_data['label'].append(res.field_description)

                            ks_list_view_records = self.env[rec.ks_model_name].read_group(ks_chart_domain, ks_list_fields,
                                                                                      [
                                                                                          rec.ks_chart_relation_groupby.name],
                                                                                      orderby=orderby, limit=limit)
                        for res in ks_list_view_records:
                            if all(list_fields in res for list_fields in ks_list_fields) and res[
                                rec.ks_chart_relation_groupby.name]:
                                counter = 0
                                data_row = {'id': res[rec.ks_chart_relation_groupby.name][0], 'data': []}
                                for field_rec in ks_list_fields:
                                    if counter == 0:
                                        data_row['data'].append(res[field_rec][1])
                                    else:
                                        data_row['data'].append(res[field_rec])
                                    counter += 1
                                ks_list_view_data['data_rows'].append(data_row)

                    elif rec.ks_chart_groupby_type == 'date_type' and rec.ks_chart_date_groupby:
                        ks_list_view_data['list_view_type'] = 'date_type'
                        ks_list_view_data[
                            'groupby'] = rec.ks_chart_relation_groupby.name + ':' + rec.ks_chart_date_groupby
                        ks_list_fields.append(rec.ks_chart_relation_groupby.name + ':' + rec.ks_chart_date_groupby)
                        ks_list_view_data['label'].append(
                            rec.ks_chart_relation_groupby.field_description + ' : ' + rec.ks_chart_date_groupby.capitalize())
                        for res in rec.ks_list_view_group_fields:
                            ks_list_fields.append(res.name)
                            ks_list_view_data['label'].append(res.field_description)

                        ks_list_view_records = self.env[rec.ks_model_name].read_group(ks_chart_domain, ks_list_fields,
                                                                                      [
                                                                                          rec.ks_chart_relation_groupby.name + ':' + rec.ks_chart_date_groupby],
                                                                                      orderby=orderby, limit=limit)
                        for res in ks_list_view_records:
                            if all(list_fields in res for list_fields in ks_list_fields):
                                counter = 0
                                data_row = {'id': 0, 'data': []}
                                for field_rec in ks_list_fields:
                                    data_row['data'].append(res[field_rec])
                                ks_list_view_data['data_rows'].append(data_row)

                rec.ks_list_view_data = json.dumps(ks_list_view_data)

    @api.multi
    @api.onchange('ks_dashboard_item_type')
    def set_color_palette(self):
        for rec in self:
            if rec.ks_dashboard_item_type == "ks_bar_chart" or rec.ks_dashboard_item_type == "ks_horizontalBar_chart" or rec.ks_dashboard_item_type == "ks_line_chart" or rec.ks_dashboard_item_type == "ks_area_chart":
                rec.ks_chart_item_color = "cool"
            else:
                rec.ks_chart_item_color = "default"
