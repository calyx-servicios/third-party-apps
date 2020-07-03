odoo.define('ks_dashboard_ninja.ks_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var viewRegistry = require('web.view_registry');
    var _t = core._t;
    var QWeb = core.qweb;
    var framework = require('web.framework');
    var time = require('web.time');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');

    var KsDashboardNinja = Widget.extend(ControlPanelMixin, {
        // To show or hide top control panel flag.
        need_control_panel: false,

        /**
         * @override
         */

        jsLibs: ['/ks_dashboard_ninja/static/lib/js/jquery.ui.touch-punch.min.js',
            '/ks_dashboard_ninja/static/lib/js/html2canvas.js',
            '/ks_dashboard_ninja/static/lib/js/jsPDF.js',
            '/ks_dashboard_ninja/static/lib/js/Chart.js',
                '/ks_dashboard_ninja/static/lib/js/Chart.min.js',
                '/ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js',
                '/ks_dashboard_ninja/static/lib/js/Chart.bundle.js',
                '/ks_dashboard_ninja/static/lib/js/gridstack.min.js',
                '/ks_dashboard_ninja/static/lib/js/gridstack.jQueryUI.min.js',
        ],
        cssLibs: ['/ks_dashboard_ninja/static/lib/css/Chart.css',
                '/ks_dashboard_ninja/static/lib/css/Chart.min.css'],

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.action_manager = parent;
            this.ksIsDashboardManager = false;
            this.ksDashboardEditMode = false;
            this.ksNewDashboardName = false;
            this.file_type_magic_word = {
                '/': 'jpg',
                'R': 'gif',
                'i': 'png',
                'P': 'svg+xml',
            };
            this.ksAllowItemClick = true;

            //Dn Filters Iitialization
            var l10n = _t.database.parameters;
            this.form_template = 'ks_dashboard_ninja_template_view';
            this.date_format = time.strftime_to_moment_format(_t.database.parameters.date_format)
            this.date_format = this.date_format.replace(/\bYY\b/g, "YYYY");
            this.datetime_format = time.strftime_to_moment_format((_t.database.parameters.date_format + ' ' + l10n.time_format))
            //            this.is_dateFilter_rendered = false;
            this.ks_date_filter_data;

            // Adding date filter selection options in dictionary format : {'id':{'days':1,'text':"Text to show"}}
            this.ks_date_filter_selections = {
                'l_none': {
                    'days': false,
                    'text': 'Date Filter'
                },
                'l_day': {
                    'days': 1,
                    'text': 'Today'
                },
                'l_week': {
                    'days': 7,
                    'text': 'Last 7 days'
                },
                'l_month': {
                    'days': 30,
                    'text': 'Last 30 days'
                },
                'l_quarter': {
                    'days': 90,
                    'text': 'Last 90 days'
                },
                'l_year': {
                    'days': 365,
                    'text': 'Last 365 days'
                },
                'l_custom': {
                    'days': 'custom_filter',
                    'text': 'Custom'
                }
            };
            // To make sure date filter show date in specific order.
            this.ks_date_filter_selection_order = ['l_day', 'l_week', 'l_month', 'l_quarter', 'l_year', 'l_custom'];

            this.ks_dashboard_id = state.params.ks_dashboard_id;

            this.gridstack_options = {
                staticGrid: true,
                float: false
            };
            this.gridstackConfig = {};
            this.grid = false;
            this.chartMeasure = {};
            this.chart_container = {};

            this.ksChartColorOptions = ['default', 'cool', 'warm', 'neon'];
            this.ksUpdateDashboardItem = this.ksUpdateDashboardItem.bind(this);
        },

        on_attach_callback: function () {
            var self = this;
            self.ksRenderDashboard();
            self.ks_set_update_interval();
        },

        ks_set_update_interval : function(){
            var self = this;
            if (self.ks_dashboard_data.ks_set_interval){
                function ksUpdateInterval() {
//                    console.log("test");
                    $.when(self.ks_fetch_data()).then(function () {
                            self.ksUpdateDashboardItem(Object.keys(self.ks_dashboard_data.ks_item_data));
                        });
                }
                self.ksUpdateDashboard = setInterval(ksUpdateInterval, self.ks_dashboard_data.ks_set_interval);
            }
        },

        // Note : this is exceptionally bind to this function.
        ksUpdateDashboardItem : function (ids) {
            var self = this;
            for (var i=0;i<ids.length;i++){
                var item_data = self.ks_dashboard_data.ks_item_data[ids[i]];
                self.grid.removeWidget(self.$el.find(".grid-stack-item[data-gs-id="+item_data.id+"]"));
                self.ksRenderDashboardItems([item_data]);
            }
            self.grid.setStatic(true);
        },

        ks_remove_update_interval : function(){
            var self = this;
            if (self.ks_dashboard_data.ks_set_interval){
                clearInterval(self.ksUpdateDashboard)
            }
        },

        on_detach_callback : function(){
            var self = this;
            self.ks_remove_update_interval();
        },

        events: {
            'click #ks_add_item_selection>li': '_onKsAdditemTypeClick',
            'click .ks_dashboard_add_layout': '_onKsAddLayoutClick',
            'click .ks_dashboard_edit_layout': '_onKsEditLayoutClick',
            'click .ks_dashboard_select_item': 'onKsSelectItemClick',
            'click .ks_dashboard_save_layout': '_onKsSaveLayoutClick',
            'click .ks_dashboard_cancel_layout': '_onKsCancelLayoutClick',
            'click .ks_item_click': '_onKsItemClick',
            //            'click .ks_dashboard_item_action': '_onKsItemActionClick',
            'click .ks_dashboard_item_customize': '_onKsItemCustomizeClick',
            'click .ks_dashboard_item_delete': '_onKsDeleteItemClick',
            'change .ks_dashboard_header_name': '_onKsInputChange',
            'click .ks_duplicate_item': 'onKsDuplicateItemClick',
            'click .ks_move_item': 'onKsMoveItemClick',
            'click .ks_dashboard_menu_container': function (e) {
                e.stopPropagation();
            },
            'show.bs.dropdown .ks_dashboard_item_button_container': 'onKsDashboardMenuContainerShow',
            'hide.bs.dropdown .ks_dashboard_item_button_container': 'onKsDashboardMenuContainerHide',
            'click .ks_dashboard_item_action': 'ksStopClickPropagation',

            //  Dn Filters Events
            'click .ks-options-btn': '_onksOptionsClick',
            'click .print-dashboard-btn': '_onKsDashboardPrint',
            'click .apply-dashboard-date-filter': '_onKsApplyDateFilter',
            'click .clear-dashboard-date-filter': '_onKsClearDateValues',
            'change #ks_start_date_picker': '_ksShowApplyClearDateButton',
            'change #ks_end_date_picker': '_ksShowApplyClearDateButton',
            'click #ks_date_selector_container>li': '_ksOnDateFilterMenuSelect',
            'click #ks_item_info': 'ksOpenItemFormView',
            'click .ks_chart_color_options': 'ksRenderChartColorOptions',
            'click #ks_chart_canvas_id': 'onChartCanvasClick',
            'click .ks_dashboard_item_chart_info': 'onChartMoreInfoClick',
            'click .chart_xls_export': 'ksChartExportXLS',
            'click .chart_pdf_export': 'ksChartExportPdf',
        },


        willStart: function () {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function () {
                return self.ks_fetch_data();
            });
        },

        start: function () {
            var self = this;
            self.set({ 'title':self.ks_dashboard_data.name})
            self.ks_set_default_chart_view();
            return this._super();
        },

        ks_set_default_chart_view: function () {
            Chart.plugins.register({
                afterDraw: function (chart) {
                    if (chart.data.labels.length === 0) {
                        // No data is present
                        var ctx = chart.chart.ctx;
                        var width = chart.chart.width;
                        var height = chart.chart.height
                        chart.clear();

                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.font = "3rem 'Lucida Grande'";
                        ctx.fillText('No data available', width / 2, height / 2);
                        ctx.restore();
                    }
                }
            });
        },

        ksRenderChartColorOptions: function (e) {
            var self = this;
            if (!$(e.currentTarget).parent().hasClass('ks_date_filter_selected')) {
                //            FIXME : Correct this later.
                var $parent = $(e.currentTarget).parent().parent();
                $parent.find('.ks_date_filter_selected').removeClass('ks_date_filter_selected')
                $(e.currentTarget).parent().addClass('ks_date_filter_selected')
                var item_data = self.ks_dashboard_data.ks_item_data[$parent.data().itemId];
                var data = $parent.data();
                this.ksChartColors(e.currentTarget.dataset.chartColor, this.chart_container[$parent.data().itemId], $parent.data().chartType, $parent.data().chartFamily, item_data.ks_bar_chart_stacked)
                this._rpc({
                    model: 'ks_dashboard_ninja.item',
                    method: 'write',
                    args: [$parent.data().itemId, {
                        "ks_chart_item_color": e.currentTarget.dataset.chartColor
                    }],
                });
            }
        },


        //To fetch dashboard data.
        ks_fetch_data: function () {
            var self = this;
            return this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_dashboard_data',
                args: [self.ks_dashboard_id],
            }).done(function (result) {
                self.ks_dashboard_data = result;
            });
        },

        on_reverse_breadcrumb: function (state) {
            var self = this;
            this.action_manager.do_push_state(state);
            return $.when(self.ks_fetch_data());
        },

        ksStopClickPropagation: function (e) {
            this.ksAllowItemClick = false;
        },

        onKsDashboardMenuContainerShow: function (e) {
            $(e.currentTarget).addClass('ks_dashboard_item_menu_show');
            this.ks_remove_update_interval();
             //            Dynamic Bootstrap menu populate Image Report
            if($(e.target).hasClass('ks_dashboard_more_action')){
                var chart_id = e.target.dataset.itemId;
                var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
                var base64_image = this.chart_container[chart_id].toBase64Image();
                $(e.target).find('.dropdown-menu').empty();
                $(e.target).find('.dropdown-menu').append($(QWeb.render('ksMoreChartOptions', {
                href: base64_image, download_fileName:name,chart_id:chart_id })))
            }
        },

        onKsDashboardMenuContainerHide: function (e) {
            $(e.currentTarget).removeClass('ks_dashboard_item_menu_show');
            this.ks_set_update_interval();
        },

        ks_get_dark_color: function (color, opacity, percent) {
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        },

        //        Number Formatter into shorthand function
        ksNumFormatter: function (num, digits) {
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
        },


        //    This is to convert color #value into RGB format to add opacity value.
        _ks_get_rgba_format: function (val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function (v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        },

        ksRenderDashboard: function () {
            var self = this;
            self.$el.empty();
            self.$el.addClass('ks_dashboard_ninja d-flex flex-column');

            var $ks_header = $(QWeb.render('ksDashboardNinjaHeader', {
                ks_dashboard_name: self.ks_dashboard_data.name,
                ks_dashboard_manager: self.ks_dashboard_data.ks_dashboard_manager,
                date_selection_data: self.ks_date_filter_selections,
                date_selection_order: self.ks_date_filter_selection_order
            }));
            self.$el.append($ks_header);

            self.ksRenderDashboardMainContent();
        },

        ksRenderDashboardMainContent: function () {
            var self = this;
            if (self.ks_dashboard_data.ks_item_data) {
                self._renderDateFilterDatePicker();
                self.$el.find('.ks_dashboard_link').removeClass("ks_hide");
                self.$el.find('.print-dashboard-btn').removeClass("ks_hide");
                $('.ks_dashboard_items_list').remove();
                var $dashboard_body_container = $(QWeb.render('ks_main_body_container'))
                var $gridstackContainer = $dashboard_body_container.find(".grid-stack");
                $dashboard_body_container.appendTo(self.$el)
                $gridstackContainer.gridstack(self.gridstack_options);
                self.grid = $gridstackContainer.data('gridstack');

                self.ksRenderDashboardItems(Object.values(self.ks_dashboard_data.ks_item_data));
            } else if (!self.ks_dashboard_data.ks_item_data) {
                 self.$el.find('.ks_dashboard_link').addClass("ks_hide");
                self._ksRenderNoItemView();
            }
        },

        ksRenderDashboardItems: function (items) {
            var self = this;
            self.$el.find('.print-dashboard-btn').addClass("ks_pro_print_hide");

            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
            }

            var item_view;
            var ks_container_class = 'grid-stack-item',
                ks_inner_container_class = 'grid-stack-item-content';
            for (var i = 0; i < items.length; i++) {
                if(self.grid){
                    if (items[i].ks_dashboard_item_type === 'ks_tile') {
                        item_view = self._ksRenderDashboardTile(items[i], ks_container_class, ks_inner_container_class)
                        if (items[i].id in self.gridstackConfig) {
                            self.grid.addWidget($(item_view), self.gridstackConfig[items[i].id].x, self.gridstackConfig[items[i].id].y, self.gridstackConfig[items[i].id].width, self.gridstackConfig[items[i].id].height, false, 11, null, 2, 2, items[i].id);
                        } else {
                            self.grid.addWidget($(item_view), 0, 0, 11, 2, true, 11, null, 2, 2, items[i].id);
                        }
                    } else if (items[i].ks_dashboard_item_type === 'ks_list_view') {
                        self._renderListView(items[i], self.grid)
                    } else {
                        self._renderGraph(items[i], self.grid)
                    }
                }
            }
            self.grid.setStatic(true);
        },

        _ksRenderDashboardTile: function (tile, ks_container_class, ks_inner_container_class) {
            var self = this;
            var ks_icon_url, item_view;
            var ks_rgba_background_color, ks_rgba_font_color, ks_rgba_default_icon_color;
            var style_main_body, style_image_body_l2, style_domain_count_body, style_button_customize_body,
                style_button_delete_body;

            var data_count = self.ksNumFormatter(tile.count, 1);
            if (tile.ks_icon_select == "Custom") {
                if (tile.icon[0]) {
                    ks_icon_url = 'data:image/' + (self.file_type_magic_word[tile.icon[0]] || 'png') + ';base64,' + tile.icon;
                } else {
                    ks_icon_url = false;
                }
            }

            tile.ksIsDashboardManager = self.ks_dashboard_data.ks_dashboard_manager;
            ks_rgba_background_color = self._ks_get_rgba_format(tile.color);
            ks_rgba_font_color = self._ks_get_rgba_format(tile.font_color);
            ks_rgba_default_icon_color = self._ks_get_rgba_format(tile.ks_default_icon_color);
            style_main_body = "background-color:" + ks_rgba_background_color + ";color : " + ks_rgba_font_color + ";";
            switch (tile.layout) {
                case 'layout1':
                    item_view = QWeb.render('ks_dashboard_item_layout1', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                case 'layout2':
                    var ks_rgba_dark_background_color_l2 = self._ks_get_rgba_format(self.ks_get_dark_color(tile.color.split(',')[0], tile.color.split(',')[1], -10));
                    style_image_body_l2 = "background-color:" + ks_rgba_dark_background_color_l2 + ";";
                    item_view = QWeb.render('ks_dashboard_item_layout2', {
                        item: tile,
                        style_image_body_l2: style_image_body_l2,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                case 'layout3':
                    item_view = QWeb.render('ks_dashboard_item_layout3', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                case 'layout4':
                    style_main_body = "color : " + ks_rgba_font_color + ";border : solid;border-width : 1px;border-color:" + ks_rgba_background_color + ";"
                    style_image_body_l2 = "background-color:" + ks_rgba_background_color + ";";
                    style_domain_count_body = "color:" + ks_rgba_background_color + ";";
                    item_view = QWeb.render('ks_dashboard_item_layout4', {
                        item: tile,
                        style_main_body: style_main_body,
                        style_image_body_l2: style_image_body_l2,
                        style_domain_count_body: style_domain_count_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                case 'layout5':
                    item_view = QWeb.render('ks_dashboard_item_layout5', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                case 'layout6':
                    ks_rgba_default_icon_color = self._ks_get_rgba_format(tile.ks_default_icon_color);
                    item_view = QWeb.render('ks_dashboard_item_layout6', {
                        item: tile,
                        style_image_body_l2: style_image_body_l2,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count
                    });
                    break;

                default:
                    item_view = QWeb.render('ks_dashboard_item_layout_default', {
                        item: tile
                    });
                    break;
            }
            return item_view;
        },

        _renderGraph: function (item, grid) {
            var self = this;
            var chart_data = JSON.parse(item.ks_chart_data);
            var chart_id = item.id,
                chart_title = item.name;
            var chart_title = item.name;
            var chart_type = item.ks_dashboard_item_type.split('_')[1];
            switch (chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                case "area":
                    var chart_family = "square"
                    break;
                default:
                    var chart_family = "none";
                    break;
            }

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', {
                ks_chart_title: chart_title,
                ksIsDashboardManager: self.ks_dashboard_data.ks_dashboard_manager,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                chart_id: chart_id,
                chart_family: chart_family,
                chart_type: chart_type,
                ksChartColorOptions: this.ksChartColorOptions
            })).addClass('ks_dashboarditem_id');
            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');
            var $ksChartContainer = $('<canvas id="ks_chart_canvas_id" data-chart-id='+chart_id+'/>');
            $ks_gridstack_container.find('.card-body').append($ksChartContainer);


            if (chart_id in self.gridstackConfig) {
                grid.addWidget($ks_gridstack_container, self.gridstackConfig[chart_id].x, self.gridstackConfig[chart_id].y, self.gridstackConfig[chart_id].width, self.gridstackConfig[chart_id].height, false, 11, null, 3, null, chart_id);
            } else {
                grid.addWidget($ks_gridstack_container, 0, 0, 11, 4, true, 11, null, 3, null, chart_id);
            }
            if(chart_family === "circle"){
                if (chart_data['labels'].length > 30){
                    $ks_gridstack_container.find(".ks_dashboard_color_option").remove();
                    $ks_gridstack_container.find(".card-body").empty().append($("<div style='font-size:18px;'>Too many records for selected Chart Type. Consider using <strong>Domain</strong> to filter records or <strong>Record Limit</strong> to limit the no of records under <strong>30.</strong>"));
                    return ;
                }
            }
            var ksMyChart = new Chart($ksChartContainer[0], {
                type: chart_type === "area" ? "line" : chart_type,
                data: {
                    labels: chart_data['labels'],
                    groupByIds:chart_data['groupByIds'],
                    datasets: chart_data.datasets,
                },
                options: {
                    maintainAspectRatio: false,
                    responsiveAnimationDuration: 1000,
                    animation: {
                        easing: 'easeInQuad',
                    }
                }
            });

            this.chart_container[chart_id] = ksMyChart;
            self.ksChartColors(item.ks_chart_item_color, ksMyChart, chart_type, chart_family, item.ks_bar_chart_stacked);
            ksMyChart.update();

        },

        ksChartColors: function (palette, ksMyChart, ksChartType, ksChartFamily, stack) {
            var currentPalette = "cool";
            if (!palette) palette = currentPalette;
            currentPalette = palette;

            /*Gradients
              The keys are percentage and the values are the color in a rgba format.
              You can have as many "color stops" (%) as you like.
              0% and 100% is not optional.*/
            var gradient;
            switch (palette) {
                case 'cool':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [220, 237, 200, 1],
                        45: [66, 179, 213, 1],
                        65: [26, 39, 62, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'warm':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [254, 235, 101, 1],
                        45: [228, 82, 27, 1],
                        65: [77, 52, 47, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'neon':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [255, 236, 179, 1],
                        45: [232, 82, 133, 1],
                        65: [106, 27, 154, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;

                case 'default':
                    var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
            }

            //Find datasets and length
            var chartType = ksMyChart.config.type;

            switch (chartType) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var datasets = ksMyChart.config.data.datasets[0];
                    var setsCount = datasets.data.length;
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                    var datasets = ksMyChart.config.data.datasets;
                    var setsCount = datasets.length;
                    break;
            }

            //Calculate colors
            var chartColors = [];

            if (palette !== "default") {
                //Get a sorted array of the gradient keys
                var gradientKeys = Object.keys(gradient);
                gradientKeys.sort(function (a, b) {
                    return +a - +b;
                });
                for (var i = 0; i < setsCount; i++) {
                    var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
                    for (var j = 0; j < gradientKeys.length; j++) {
                        var gradientKey = gradientKeys[j];
                        if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
                            chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
                            break;
                        } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
                            var prevKey = gradientKeys[j - 1];
                            var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
                            var color = [];
                            for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
                                color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
                                if (k < 3) color[k] = Math.round(color[k]);
                            }
                            chartColors[i] = 'rgba(' + color.toString() + ')';
                            break;
                        }
                    }
                }
            } else {
                for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
                    if (counter >= color_set.length) counter = 0; // reset back to the beginning

                    chartColors.push(color_set[counter]);
                }
            }

            var datasets = ksMyChart.config.data.datasets;
            var options = ksMyChart.config.options;

            options.legend.labels.usePointStyle = true;
            if (ksChartFamily == "circle") {
                options.legend.position = 'bottom';
                options.tooltips.callbacks = {
                                              title: function(tooltipItem, data) {
                                                          return data.datasets[tooltipItem[0].datasetIndex]['label']+" : "+data.datasets[tooltipItem[0].datasetIndex]['data'][tooltipItem[0].index];
                                                        },
                                               label : function(tooltipItem, data) {
                                                          return data.labels[tooltipItem.index];
                                                        },
                                                }
                for (var i = 0; i < datasets.length; i++) {
                    datasets[i].backgroundColor = chartColors;
                    datasets[i].borderColor = "rgba(255,255,255,1)";
                }
            } else if (ksChartFamily == "square") {
                options.scales.xAxes[0].gridLines.display = false;
                options.scales.yAxes[0].ticks.beginAtZero = true;
                for (var i = 0; i < datasets.length; i++) {
                    switch (ksChartType) {
                        case "bar":
                        case "horizontalBar":
                            if (datasets[i].type && datasets[i].type=="line"){
                                datasets[i].borderColor = chartColors[i];
                                datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            }
                            else{
                                datasets[i].backgroundColor = chartColors[i];
                                datasets[i].borderColor = "rgba(255,255,255,0)";
                                options.scales.xAxes[0].stacked = stack;
                                options.scales.yAxes[0].stacked = stack;
                            }
                            break;
                        case "line":
                            datasets[i].borderColor = chartColors[i];
                            datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            break;
                        case "area":
                            datasets[i].borderColor = chartColors[i];
                            break;
                    }
                }
            }
            ksMyChart.update();
        },

        onChartCanvasClick : function(evt){
            var self = this;
            var item_id = evt.currentTarget.dataset.chartId;
            var myChart = self.chart_container[item_id];
            var activePoint = myChart.getElementAtEvent(evt)[0];
            if (activePoint){
                var item_data = self.ks_dashboard_data.ks_item_data[item_id];

                var groupBy = item_data.ks_chart_groupby_type==='relational_type'?item_data.ks_chart_relation_groupby:item_data.ks_chart_relation_groupby+':'+item_data.ks_chart_date_groupby;
                var domain = JSON.parse(item_data.domain);
                var action = {
                    name: _t(item_data.name),
                    type: 'ir.actions.act_window',
                    res_model: item_data.model_id,
                    domain: domain || [],
                    context: {
                        'group_by':groupBy,
                    },
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    view_mode: 'list',
                    target: 'current',
                }
                if(activePoint._chart.data.groupByIds){
                    action['context']['search_default_'+groupBy] = activePoint._chart.data.groupByIds[activePoint._index];
                }
                self.do_action(action, {
                                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                                });
            }
        },

        onChartMoreInfoClick : function(evt){
            var self = this;
            var item_id = evt.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var groupBy = item_data.ks_chart_groupby_type==='relational_type'?item_data.ks_chart_relation_groupby:item_data.ks_chart_relation_groupby+':'+item_data.ks_chart_date_groupby;
            var domain = JSON.parse(item_data.domain);
            var action = {
                    name: _t(item_data.name),
                    type: 'ir.actions.act_window',
                    res_model: item_data.model_id,
                    domain: domain || [],
                    context: {
                        'group_by':groupBy,
                    },
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    view_mode: 'list',
                    target: 'current',
                }
            self.do_action(action, {
                                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                            });

        },


        _ksRenderNoItemView: function () {
            var self = this;
            $(QWeb.render('ksNoItemView')).appendTo(self.$el)
        },

        _ksRenderEditMode: function () {
            var self = this;
            self.ks_remove_update_interval();
            $('#ks_dashboard_title_input').val(self.ks_dashboard_data.name);

            $('.ks_am_element').addClass("ks_hide");
            $('.ks_em_element').removeClass("ks_hide");

            self.$el.find('.ks_item_click').addClass('ks_item_not_click').removeClass('ks_item_click');
            self.$el.find('.ks_dashboard_item').removeClass('ks_dashboard_item_header_hover');
            self.$el.find('.ks_dashboard_item_header').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_l2').removeClass('ks_dashboard_item_header_hover');
            self.$el.find('.ks_dashboard_item_header_l2').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_l5').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_button_container').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_link').addClass("ks_hide")
            self.$el.find('.ks_dashboard_top_settings').addClass("ks_hide")
            self.$el.find('.ks_dashboard_edit_mode_settings').removeClass("ks_hide")

            // Adding Chart grab able cals
            self.$el.find('.ks_chart_container').addClass('ks_item_not_click');
            self.$el.find('.ks_list_view_container').addClass('ks_item_not_click');

            if (self.grid) {
                self.grid.enable();
            }
        },


        _ksRenderActiveMode: function () {
            var self = this

            if (self.grid) {
                $('.grid-stack').data('gridstack').disable();
            }

            $('#ks_dashboard_title_label').text(self.ks_dashboard_data.name);

            $('.ks_am_element').removeClass("ks_hide");
            $('.ks_em_element').addClass("ks_hide");
            if (self.ks_dashboard_data.ks_item_data) $('.ks_am_content_element').removeClass("ks_hide");

            self.$el.find('.ks_item_not_click').addClass('ks_item_click').removeClass('ks_item_not_click')
            self.$el.find('.ks_dashboard_item').addClass('ks_dashboard_item_header_hover')
            self.$el.find('.ks_dashboard_item_header').addClass('ks_dashboard_item_header_hover')

            self.$el.find('.ks_dashboard_item_l2').addClass('ks_dashboard_item_header_hover')
            self.$el.find('.ks_dashboard_item_header_l2').addClass('ks_dashboard_item_header_hover')

            //      For layout 5
            self.$el.find('.ks_dashboard_item_l5').addClass('ks_dashboard_item_header_hover')


            self.$el.find('.ks_dashboard_item_button_container').addClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_top_settings').removeClass("ks_hide")
            self.$el.find('.ks_dashboard_edit_mode_settings').addClass("ks_hide")

            self.$el.find('.ks_chart_container').removeClass('ks_item_not_click ks_item_click');
            self.ks_set_update_interval();
        },

        _ksToggleEditMode: function () {
            var self = this
            if (self.ksDashboardEditMode) {
                self._ksRenderActiveMode()
                self.ksDashboardEditMode = false
            } else if (!self.ksDashboardEditMode) {
                self._ksRenderEditMode()
                self.ksDashboardEditMode = true
            }

        },

        _onKsAddLayoutClick: function () {
            var self = this;

            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.item',
                view_id: 'ks_dashboard_ninja_list_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'current',
                context: {
                    'ks_dashboard_id': self.ks_dashboard_id
                },
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },

        _onKsEditLayoutClick: function () {
            var self = this;
            self._ksRenderEditMode();
        },

        //TODO: Remove this or Use this
        onKsSelectItemClick: function () {},

        _onKsSaveLayoutClick: function () {
            var self = this;
            //        Have  to save dashboard here
            var dashboard_title = $('#ks_dashboard_title_input').val();
            if (dashboard_title != false && dashboard_title != 0 && dashboard_title !== self.ks_dashboard_data.name) {
                self.ks_dashboard_data.name = dashboard_title;
                this._rpc({
                    model: 'ks_dashboard_ninja.board',
                    method: 'write',
                    args: [self.ks_dashboard_id, {
                        'name': dashboard_title
                    }],
                })
            }
            if(this.ks_dashboard_data.ks_item_data) self._ksSaveCurrentLayout();
            self._ksRenderActiveMode();
        },

        _onKsCancelLayoutClick: function () {
            var self = this;
            //        render page again
            self.ksRenderDashboard();
        },

        _onKsItemClick: function (e) {
            var self = this;
            //            To Handle only allow item to open when not clicking on item
            if (self.ksAllowItemClick) {
                e.preventDefault();
                if (e.target.title != "Customize Item") {
                    var id = parseInt(e.currentTarget.firstElementChild.id);
                    this._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'read',
                        args: [id, ['ks_model_name', 'ks_domain']],
                    }).then(function (data) {
                        if (data[0].ks_model_name) {
                            self.do_action({
                                name: _t('Selected records'),
                                type: 'ir.actions.act_window',
                                res_model: data[0].ks_model_name,
                                domain: data[0].ks_domain || "[]",
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                view_mode: 'list',
                                target: 'current',
                            }, {
                                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                            });
                        } else {
                            alert(_t("No module defined for current dashboard item."))
                        }
                    })
                }
            } else {
                self.ksAllowItemClick = true;
            }
        },

        _onKsItemCustomizeClick: function (e) {
            var self = this;
            var id = parseInt($($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0]).attr('data-gs-id'))
            self.ks_open_item_form_page(id);

            e.stopPropagation();
        },

        ks_open_item_form_page: function (id) {
            var self = this;
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.item',
                view_id: 'ks_dashboard_ninja_list_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'current',
                res_id: id
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },

        _onKsDeleteItemClick: function (e) {
            var self = this;
            var id = parseInt($($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0]).attr('data-gs-id'))
            self.ks_delete_item(id);
            e.stopPropagation();
        },

        ks_delete_item: function (id) {
            var self = this;
            Dialog.confirm(this, (_t("Are you sure you want to remove this item?")), {
                confirm_callback: function () {

                    self._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'unlink',
                        args: [id],
                    }).then(function (data) {
                        $.when(self.ks_fetch_data()).then(function () {
                            $('.ks_dashboard_items_list').remove();
                            self.ksRenderDashboardMainContent();
                            if(self.ks_dashboard_data.ks_item_data) self._ksSaveCurrentLayout();
                        });
                    });
                },
            });

        },

        _ksSaveCurrentLayout: function () {
            var self = this;
            var items = $('.grid-stack').data('gridstack').grid.nodes;
            var grid_config = {}
            for (var i = 0; i < items.length; i++) {
                grid_config[items[i].id] = {
                    'x': items[i].x,
                    'y': items[i].y,
                    'width': items[i].width,
                    'height': items[i].height
                }
            }
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'write',
                args: [self.ks_dashboard_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config)
                }],
            });
        },

        _renderListView: function (item, grid) {
            var self = this;
            var list_view_data = JSON.parse(item.ks_list_view_data);
            var item_id = item.id,
                item_title = item.name;

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_list_view_container', {
                ks_chart_title: item_title,
                ksIsDashboardManager: self.ks_dashboard_data.ks_dashboard_manager,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list
            })).attr("id", item_id).addClass('ks_dashboarditem_id');
            var $ksItemContainer = $(QWeb.render('ks_list_view_table', {
                list_view_data: list_view_data
            }));
            $ks_gridstack_container.find('.card-body').append($ksItemContainer);

            if (item_id in self.gridstackConfig) {
                grid.addWidget($ks_gridstack_container, self.gridstackConfig[item_id].x, self.gridstackConfig[item_id].y, self.gridstackConfig[item_id].width, self.gridstackConfig[item_id].height, false, 9, null, 3, null, item_id);
            } else {
                grid.addWidget($ks_gridstack_container, 0, 0, 13, 4, true, 9, null, 3, null, item_id);
            }
        },

        _onKsInputChange: function (e) {
            this.ksNewDashboardName = e.target.value
        },

        onKsDuplicateItemClick: function (e) {
            var self = this;
            var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id')
            var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').val()
            var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text()

            this._rpc({
                model: 'ks_dashboard_ninja.item',
                method: 'copy',
                args: [parseInt(ks_item_id), {
                    'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
                }],
            }).then(function (result) {
                self.do_notify(
                    _t("Item Duplicated"),
                    _t('Selected item is duplicated to '+dashboard_name+' .')
                );
                $.when(self.ks_fetch_data()).then(function () {
                    self.ksRenderDashboard();
                });
            })
        },

        ksOpenItemFormView: function (e) {
            var self = this;
            self.do_action({
                name: _t('Selected record'),
                type: 'ir.actions.act_window',
                res_model: e.currentTarget.dataset.model,
                domain: "[]",
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                res_id: parseInt(e.currentTarget.dataset.recordId),
                target: 'current',
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },

        onKsMoveItemClick: function (e) {
            var self = this;
            var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id')
            var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').val()
            var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text()

            this._rpc({
                model: 'ks_dashboard_ninja.item',
                method: 'write',
                args: [parseInt(ks_item_id), {
                    'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
                }],
            }).then(function (result) {
                self.do_notify(
                    _t("Item Moved"),
                    _t('Selected item is moved to '+dashboard_name+' .')
                );
                $.when(self.ks_fetch_data()).then(function () {
                    self.ksRenderDashboard();
                });
            })
        },

        _KsGetDateValues: function () {
            var self = this;
            var date_format = time.strftime_to_moment_format(_t.database.parameters.date_format);
            var check_format = date_format.search(/YYYY/);
            if (!(check_format !== -1)) {
                date_format = date_format.replace(/YY/g, "YYYY");
            }
            var date_filter_selected = self.ks_dashboard_data.ks_date_filter_selection;
            self.$el.find('#' + date_filter_selected).addClass("ks_date_filter_selected");
            self.$el.find('#ks_date_filter_selection').text(self.ks_date_filter_selections[date_filter_selected]["text"]);
            if (self.ks_dashboard_data.ks_dashboard_start_date && self.ks_dashboard_data.ks_dashboard_start_date) {
                self.ks_start_date = self.ks_dashboard_data.ks_dashboard_start_date.split(' ')[0];
                self.$el.find("#ksActualStartDateToStore").val(self.ks_start_date);
                self.ks_end_date = self.ks_dashboard_data.ks_dashboard_end_date.split(' ')[0];
                self.$el.find("#ksActualEndDateToStore").val(self.ks_start_date);
                self.ks_start_date = moment(self.ks_start_date).format(date_format);
                self.ks_end_date = moment(self.ks_end_date).format(date_format);
                self.$el.find("#ks_start_date_picker").val(self.ks_start_date);
                self.$el.find("#ks_end_date_picker").val(self.ks_end_date);
            } else {
                self.ks_start_date = self.ks_end_date = null;
            }
            if (self.ks_dashboard_data.ks_date_filter_selection === 'l_custom' && self.ks_dashboard_data.ks_dashboard_list) {
                self.$el.find('.ks_date_input_fields').removeClass("ks_hide");
                self.$el.find('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
            } else if (self.ks_dashboard_data.ks_date_filter_selection !== 'l_custom' && self.ks_dashboard_data.ks_dashboard_list) {
                self.$el.find('.ks_date_input_fields').addClass("ks_hide");
            }
        },

        _onKsClearDateValues: function () {
            var self = this;
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'write',
                args: [self.ks_dashboard_id, {
                    "ks_dashboard_start_date": false,
                    "ks_dashboard_end_date": false,
                    "ks_date_filter_selection": 'l_none',
                }],
            }).then(function (data) {
                $.when(self.ks_fetch_data()).then(function () {
                    self.ksRenderDashboard();
                });
            });
        },

        _checkDateFields: function () {
            if (!($("#ks_start_date_picker").val())) {
                $("#ks_start_date_picker").val($("#ks_end_date_picker").val());
                $("#ksActualStartDateToStore").val($("#ksActualEndDateToStore").val());
            }
            if (!($("#ks_end_date_picker").val())) {
                $("#ks_end_date_picker").val($("#ks_start_date_picker").val());
                $("#ksActualEndDateToStore").val($("#ksActualStartDateToStore").val());
            }
        },

        _renderDateFilterDatePicker: function () {
            var self = this;

            //Show Print option cause items are present.
            self.$el.find(".ks_dashboard_link").removeClass("ks_hide");

            //Initialization of the date picker with on-select event
            self.$el.find("#ks_start_date_picker").datepicker({
                dateFormat: "yy/mm/dd",
                altFormat: "yy-mm-dd",
                altField: "#ksActualStartDateToStore",
                changeMonth: true,
                changeYear: true,
                language: moment.locale(),
                onSelect: function (ks_start_date) {
                    self.$el.find(".apply-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find("#ks_start_date_picker").val(moment(new Date(ks_start_date)).format(self.date_format));
                    self._checkDateFields();
                },
            });

            self.$el.find("#ks_end_date_picker").datepicker({
                dateFormat: "yy/mm/dd",
                altFormat: "yy-mm-dd",
                altField: "#ksActualEndDateToStore",
                changeMonth: true,
                changeYear: true,
                language: moment.locale(),
                onSelect: function (ks_end_date) {
                    self.$el.find(".apply-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find("#ks_end_date_picker").val(moment(new Date(ks_end_date)).format(self.date_format));
                    self._checkDateFields();
                },
            });
            self._KsGetDateValues();
            $('#ui-datepicker-div').addClass('ks_dashboard_datepicker_z-index');
        },

        _onKsApplyDateFilter: function (e) {
            var self = this;
            var date_format = time.strftime_to_moment_format(_t.database.parameters.date_format);
            var check_format = date_format.search(/YYYY/);
            if (!(check_format !== -1)) {
                date_format = date_format.replace(/YY/g, "YYYY");
            }
            var start_date = self.$el.find("#ksActualStartDateToStore").val();
            var end_date = self.$el.find("#ksActualEndDateToStore").val();
            if (start_date === "Invalid date") {
                alert("Invalid Date is given in Start Date.")
            } else if (end_date === "Invalid date") {
                alert("Invalid Date is given in End Date.")
            } else if (self.$el.find('.ks_date_filter_selected').attr('id') !== "l_custom") {

                this._rpc({
                    model: 'ks_dashboard_ninja.board',
                    method: 'write',
                    args: [self.ks_dashboard_id, {
                        "ks_date_filter_selection": self.$el.find('.ks_date_filter_selected').attr('id'),
                    }],
                }).then(function (data) {
                    $.when(self.ks_fetch_data()).then(function () {
                        self.ksRenderDashboard();
                    });
                });
            } else {
                start_date = start_date + " 00:00:00";
                end_date = end_date + " 23:59:59";
                if (start_date && end_date) {
                    if (start_date < end_date) {
                        this._rpc({
                            model: 'ks_dashboard_ninja.board',
                            method: 'write',
                            args: [self.ks_dashboard_id, {
                                "ks_dashboard_start_date": start_date,
                                "ks_dashboard_end_date": end_date,
                                "ks_date_filter_selection": self.$el.find('.ks_date_filter_selected').attr('id')
                            }],
                        }).then(function (data) {
                            $.when(self.ks_fetch_data()).then(function () {
                                self.ksRenderDashboard();
                            });
                        });
                    } else {
                        alert(_t("Start date should be less than end date"));
                    }
                } else {
                    alert(_t("Please enter start date and end date"));
                }
            }
        },

        _onKsToggleMenu: function (e) {
            if (!(self.$el.find(".ks_dashboard_links").hasClass("d-flex"))) {
                self.$el.find(".ks_dashboard_links").addClass('d-flex');
            } else {
                self.$el.find(".ks_dashboard_links").removeClass('d-flex');
            }
        },

        //Click event for dashboard print button. Will print pdf of current dashboard.
        _onKsDashboardPrint: function (e) {
            var self = this;
            framework.blockUI();
            this.ksPrepareViewBeforePrint();
            var current_date = $.datepicker.formatDate('yy/mm/dd', new Date());
            var report_name = this.ks_dashboard_data.name + "_" + current_date
            html2canvas($(this.$el.context), {
                //To show logs in console related to dashboard, uncomment below line
                //logging: true,
                profile: true,
                useCORS: true,
                allowTaint: true
            }).then(function (canvas) {
                var ks_img = canvas.toDataURL('image/png');
                var doc = new jsPDF('p', 'mm');
                doc.addImage(ks_img, 'PNG', 5, 10, 200, 0);
                doc.save(report_name);
                framework.unblockUI();
                $.when(self.ks_fetch_data()).then(function () {
                    self.ksRenderDashboard();
                });
            });
        },

        //This will change the view temporarily to pdf print format
        ksPrepareViewBeforePrint: function () {
            $(".ks_dashboard_add_layout").css("display", "none");
            $(".ks_dashboard_edit_layout").css("display", "none");
            $(".apply-dashboard-date-filter").css("display", "none");
            $(".clear-dashboard-date-filter").css("display", "none");
            $(".ks_date_selection_box").css("display", "none");
            $(".ks_date_input_fields").removeClass("ks_hide");
            $(".ks-dashboard-date-labels").removeClass("ks_hide");
            $(".ks_start_date_picker").removeClass("ks_btn_middle_child");
            $(".ks_end_date_picker").removeClass("ks_btn_last_child");
            if ($(".ks_dashboard_links").hasClass("d-flex")) {
                $(".ks_dashboard_links").removeClass('d-flex');
            }
            $(".print-dashboard-btn").css("display", "none");
            $(".ks_dashboard_ninja_toggle_menu").addClass("ks_hide");
            $("#ks_start_date_picker").val(this.ks_start_date);
            $("#ks_end_date_picker").val(this.ks_end_date);
            $(".ks_header_container_div").css("background", "transparent");
            $(".ks_date_apply_clear_print").addClass("ks_hide");

            //To use same font style in pdf print as in dashboard
            $(this.$el.context).css('font-family', 'Helvetica');
        },

        //This will revert view to its default view after pdf is generated.
        ksPrepareViewAfterPrint: function () {
            self.ksRenderDashboard;
        },

        _ksShowApplyClearDateButton: function () {
            if ($("#ks_start_date_picker").val() && $("#ks_end_date_picker").val()) {
                $(".apply-dashboard-date-filter").removeClass("ks_hide");
                $(".clear-dashboard-date-filter").removeClass("ks_hide");
            } else {
                $(".apply-dashboard-date-filter").addClass("ks_hide");
                $(".clear-dashboard-date-filter").addClass("ks_hide");
            }
        },

        _ksOnDateFilterMenuSelect: function (e) {
            if (e.target.id !== 'ks_date_selector_container') {
                var self = this;
                _.each($('.ks_date_filter_selected'), function ($filter_options) {
                    $($filter_options).removeClass("ks_date_filter_selected")
                });
                $(e.target.parentElement).addClass("ks_date_filter_selected");
                $('#ks_date_filter_selection').text(self.ks_date_filter_selections[e.target.parentElement.id]["text"]);

                if (e.target.parentElement.id !== "l_custom") {
                    $('.ks_date_input_fields').addClass("ks_hide");
                    $('.ks_date_filter_dropdown').removeClass("ks_btn_first_child_radius");
                    e.target.parentElement.id === "l_none" ? self._onKsClearDateValues() : self._onKsApplyDateFilter();
                } else if (e.target.parentElement.id === "l_custom") {
                    $("#ks_start_date_picker").val(null).removeClass("ks_hide");
                    $("#ks_end_date_picker").val(null).removeClass("ks_hide");
                    $('.ks_date_input_fields').removeClass("ks_hide");
                    $('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
                }
            }
        },

        _onKsAdditemTypeClick : function(e){
            var self = this;
            var context = {};
            context['ks_dashboard_id'] = self.ks_dashboard_id;
            context['ks_dashboard_item_type'] = e.currentTarget.dataset.item;
            self.do_action({
            type : 'ir.actions.act_window',
            res_model : 'ks_dashboard_ninja.item',
            view_id : 'ks_dashboard_ninja_list_form_view',
            views : [
                [false, 'form']
            ],
            target : 'current',
            context :context,

            },{
            on_reverse_breadcrumb : this.on_reverse_breadcrumb,
            });
        },

        ksChartExportXLS : function(e){
           var chart_id = e.currentTarget.dataset.chartId;
           var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
           var data = {
                        "header":name,
                        "chart_data":this.ks_dashboard_data.ks_item_data[chart_id].ks_chart_data,
                      }
                framework.blockUI();
                this.getSession().get_file({
                    url: '/ks_dashboard_ninja/export/'+e.currentTarget.dataset.format,
                    data: {data:JSON.stringify(data)},
                    complete: framework.unblockUI,
                    error: crash_manager.rpc_error.bind(crash_manager),
                });
        },

        ksChartExportPdf : function(e){
            console.log("pdf print");
            var chart_id = e.currentTarget.dataset.chartId;
            var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
            var base64_image = this.chart_container[chart_id].toBase64Image();
            var doc = new jsPDF('p', 'mm');
            doc.addImage(base64_image, 'PNG', 5, 10, 200, 0);
            doc.save(name);
        }

    });

    core.action_registry.add('ks_dashboard_ninja', KsDashboardNinja);

    return KsDashboardNinja;
});