odoo.define('website_customer_order_delivery_date.payment', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function() {
        try {
            $("#delivery_date").datepicker({
                minDate: new Date()
            });
        } catch (e) {}

        $("#delivery_date_icon").click(function(){
            $('#delivery_date').datepicker('show');
        });

        $("button#o_payment_form_pay").bind("click", function(ev) {

            var customer_order_delivery_date = $('#delivery_date').val();
            var customer_order_delivery_comment = $('#delivery_comment').val();
            ajax.jsonRpc('/shop/customer_order_delivery', 'call', {
                'delivery_date': customer_order_delivery_date,
                'delivery_comment': customer_order_delivery_comment
            });
        });
    });

});