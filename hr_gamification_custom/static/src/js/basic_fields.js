odoo.define('percent_field.basic_fields', function (require) {
    "use strict";
    var ks_field_registry = require('web.field_registry');
    var ks_basic_fields = require('web.basic_fields');
    var ks_FieldFloat = ks_basic_fields.FieldFloat;
    var Widget = require('web.Widget');
    var ks_FieldPercent = ks_FieldFloat.extend({
        formatType:'Percent',
        supportedFieldTypes: ['float'],
    });
    ks_field_registry
        .add('Percent', ks_FieldPercent);
    return {
        ks_FieldPercent: ks_FieldPercent
    };
});

