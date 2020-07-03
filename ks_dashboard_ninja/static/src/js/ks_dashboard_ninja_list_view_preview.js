odoo.define('ks_dashboard_ninja_list.ks_dashboard_ninja_list_view_preview', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;

    var KsListViewPreview = AbstractField.extend({
        supportedFieldTypes: ['char'],

        resetOnAnyFieldChange: true,

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.state = {};
        },

        _render: function () {
            this.$el.empty()
            if (this.recordData.ks_dashboard_item_type === 'ks_list_view') {
                if(this.recordData.ks_list_view_type ===  'ungrouped'){
                    if (this.recordData.ks_list_view_fields.count !== 0) {
                        this.ksRenderListView()
                    } else {
                        this.$el.append($('<div>').text("Select Fields to show in list view."));

                    }
                } else if(this.recordData.ks_list_view_type ===  'grouped'){
                    if(this.recordData.ks_chart_relation_groupby && this.recordData.ks_list_view_group_fields.count !== 0){
                        this.ksRenderListView()
                    }else {
                        this.$el.append($('<div>').text("Select Fields and Group By to show in list view"));
                    }
                }
            }
        },

        ksRenderListView: function () {
            var field = this.recordData;
            var ks_list_view_name;
            if (field.name) ks_list_view_name = field.name;
            else if (field.ks_model_name) ks_list_view_name = field.ks_model_id.data.display_name;
            else ks_list_view_name = "Name";

            var list_view_data;
            if (field.ks_list_view_data) list_view_data = JSON.parse(field.ks_list_view_data);
            else list_view_data = false;

            var $listViewContainer = $(QWeb.render('ks_list_view_container', {
                ks_list_view_name: ks_list_view_name,
                list_view_data: list_view_data
            }));
            this.$el.append($listViewContainer);

        },

    });
    registry.add('ks_dashboard_list_view_preview', KsListViewPreview);

    return {
        KsListViewPreview: KsListViewPreview,
    };

});