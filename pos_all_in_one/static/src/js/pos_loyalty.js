odoo.define('pos_all_in_one.pos_loyalty', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var utils = require('web.utils');
	var rpc = require('web.rpc');
	var QWeb = core.qweb;
	var _t = core._t;
	var redeem;
	var point_value = 0;
	var remove_line;
	var remove_true = false;
	var entered_code;

	// Load Models
	models.load_models({
		model: 'pos.loyalty.setting',
		fields: ['name', 'product_id', 'issue_onlydate', 'expiry_onlydate', 'loyalty_basis_on', 'loyality_amount', 'active','redeem_ids'],
		domain: function(self) 
				{
					var today = new Date();
					var dd = today.getDate();
					var mm = today.getMonth()+1; //January is 0!

					var yyyy = today.getFullYear();
					if(dd<10){
						dd='0'+dd;
					} 
					if(mm<10){
						mm='0'+mm;
					} 
					var today = yyyy+'-'+mm+'-'+dd;
					return [['issue_onlydate', '<=',today],['expiry_onlydate', '>=',today]];
				},

		loaded: function(self, pos_loyalty_setting) {
			self.pos_loyalty_setting = pos_loyalty_setting;
		},
	});

	models.load_models({
		model: 'pos.redeem.rule',
		fields: ['reward_amt','min_amt','max_amt','loyality_id'],
		loaded: function(self, pos_redeem_rule) {
			self.pos_redeem_rule = pos_redeem_rule;
		},
	});

	models.load_fields('pos.category', ['Minimum_amount']);
		
	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		initialize: function (session, attributes) {
			var partner_model = _.find(this.models, function(model){ return model.model === 'res.partner'; });
			partner_model.fields.push('loyalty_points','loyalty_amount');

			return _super_posmodel.initialize.call(this, session, attributes);
			
		},
	});
	
	var _super = models.Order;
	var OrderSuper = models.Order;
	models.Order = models.Order.extend({

		initialize: function(attributes, options) {
			OrderSuper.prototype.initialize.apply(this, arguments);
			this.set({ redeem_done: false });
			this.loyalty = this.loyalty  || 0;
			this.redeemed_points = this.redeemed_points || 0;		
		},
		
		remove_orderline: function(line) {
			this.set('redeem_done', false);
			_super.prototype.remove_orderline.apply(this, arguments);
		},

		get_redeemed_points: function() {
			return parseInt(this.redeemed_points);
		},

		get_total_loyalty: function() {
			var utils = require('web.utils');
			var round_pr = utils.round_precision;
			var round_di = utils.round_decimals;
			var rounding = this.pos.currency.rounding;
			var final_loyalty = 0
			var order = this.pos.get_order();
			if(order == null){
				return
			}
			var orderlines = this.get_orderlines();
			var partner_id = this.get_client();


			if(this.pos.pos_loyalty_setting.length != 0)
			{	
			   if (this.pos.pos_loyalty_setting[0].loyalty_basis_on == 'pos_category') {
					if (partner_id)
					{
						var loyalty = 0
		
						for (var i = 0; i < orderlines.length; i++) {
							var lines = orderlines[i];
							var cat_ids = this.pos.db.get_category_by_id(lines.product.pos_categ_id[0])
							if(cat_ids){
								if (cat_ids['Minimum_amount']>0)
								{
									final_loyalty += parseInt((lines.price * lines.quantity) / cat_ids['Minimum_amount']);
								}
							}
							
						}
						return Math.floor(final_loyalty);

					}
			   }else if (this.pos.pos_loyalty_setting[0].loyalty_basis_on == 'amount') {
					
					
					var loyalty_total = 0
					if (order && partner_id)
					{
						var amount_total = order.get_total_with_tax();
						var subtotal = order.get_total_without_tax();
						var loyaly_points = this.pos.pos_loyalty_setting[0].loyality_amount;
						final_loyalty += (amount_total / loyaly_points);
						loyalty_total = order.get_client().loyalty_points + final_loyalty;
						return Math.floor(final_loyalty);
					}
				}
			}
		
		},

		export_as_JSON: function() {
			var json = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
			json.redeemed_points = parseInt(this.redeemed_points);
			json.loyalty = this.get_total_loyalty();
			json.redeem_done = this.get('redeem_done');
			return json;
		},

		init_from_JSON: function(json){
			OrderSuper.prototype.init_from_JSON.apply(this,arguments);
			this.loyalty = json.loyalty;
			this.redeem_done = json.redeem_done;
			this.redeemed_points = json.redeemed_points;
		},

	});

	var OrderWidgetExtended = screens.OrderWidget.include({

		orderline_remove: function(line){
			var order = this.pos.get_order();
			var partner = order.get_client();

			this.remove_orderline(line);
			this.numpad_state.reset();
			if(line.id == remove_line)
			{
				remove_true = true;
				partner.loyalty_points = parseInt(partner.loyalty_points) + parseInt(entered_code);
			}
			else
			{
				remove_true = false;
			}
			
			this.update_summary();

		},

		update_summary: function(){
			this._super();
			var order = this.pos.get_order();
			var partner = order.get_client();
			var temp_loyalty_point = 0;
			if(partner)
				temp_loyalty_point = partner.loyalty_points
			
			if(this.pos.pos_loyalty_setting.length != 0)
			{
				if (partner) {
					if(remove_true == true)
					{
						partner.loyalty_points = partner.loyalty_points
						order.set('update_after_redeem',partner.loyalty_points)
					}
					else{
						if(order.get('update_after_redeem') >= 0){
							partner.loyalty_points = order.get("update_after_redeem");
						}else{
							partner.loyalty_points = partner.loyalty_points
						}
					}

					var loyalty_points = 0
					loyalty_points    = order ? order.get_total_loyalty() : 0;
					temp_loyalty_point = partner.loyalty_points + loyalty_points ;    
					if(this.el.querySelector('.items')){
						this.el.querySelector('.items').style.display = 'inline-block'
						this.el.querySelector('.items .loyalty').textContent = loyalty_points;
						this.el.querySelector('.items .loyalty_value').textContent = temp_loyalty_point;
					}
					order.set("temp_loyalty_point",temp_loyalty_point)
				}
			}

		},
	});
	
	

	// LoyaltyPopupWidget start
	var LoyaltyPopupWidget = popups.extend({
		template: 'LoyaltyPopupWidget',
		init: function(parent, args) {
			this._super(parent, args);
			this.options = {};
		},
		show: function(options) {
			options = options || {};
			var self = this;
			this._super(options);
			
			var order = this.pos.get_order();
			
			var partner = false
			if (order.get_client() != null)
				partner = order.get_client();
						   
			if (partner) {
				this.partner = options.partner.name || {};
				var curr_loyalty_points = 0
				partner.loyalty_amount = point_value;
				self.loyalty = partner.loyalty_points;
				self.loyalty_amount = point_value;
				self.renderElement();
							
			}else{
				self.gui.show_popup('error', {
					'title': _t('Unknown customer'),
					'body': _t('You cannot use redeeming loyalty points. Select customer first.'),
				});
				
			}
				
		},

		renderElement: function() {
			var self = this;
			this._super();
			var order = this.pos.get_order();
			var selectedOrder = self.pos.get('selectedOrder');
			if(selectedOrder == null){
				return
			}
			var orderlines = selectedOrder.orderlines;
			var update_orderline_loyalty = 0 ;
			 

			var partner = false
			if (order && order.get_client() != null){
				partner = order.get_client();
					
				var loyalty = order.get_client().loyalty_points;
				var total     = order.get_total_with_tax();
			}               
			if(this.pos.pos_loyalty_setting.length != 0)
			{
				var product_id = this.pos.pos_loyalty_setting[0].product_id[0];
				var product = this.pos.db.get_product_by_id(product_id);


				if(this.pos.pos_loyalty_setting[0].redeem_ids.length != 0)
				{
					var redeem_arr = []
					for (var i = 0; i < this.pos.pos_loyalty_setting[0].redeem_ids.length; i++) {
						for (var j = 0; j < this.pos.pos_redeem_rule.length; j++) {
							if(this.pos.pos_loyalty_setting[0].redeem_ids[i] == this.pos.pos_redeem_rule[j].id)
							{
								redeem_arr.push(this.pos.pos_redeem_rule[j]);
							}
						}
					}
					for (var j = 0; j < redeem_arr.length; j++) {
						if( parseInt(redeem_arr[j].min_amt) <= parseInt(partner.loyalty_points) && parseInt(partner.loyalty_points) <= parseInt(redeem_arr[j].max_amt))
						{
							redeem = redeem_arr[j];
							break;
						}
					}
					if(redeem)
					{
						point_value = parseInt(redeem.reward_amt) * parseInt(loyalty);
						if (partner){
							partner.loyalty_amount = point_value;
						}
					}
					
				}
			}
			this.$('#apply_redeem_now').click(function() {
				entered_code = $("#entered_item_qty").val();
				remove_true = false
				if(parseInt(partner.loyalty_points) <= 0 )
				{
					alert(partner.name + " : has no sufficient points to redeem")
					return;
				}
				if(parseInt(entered_code) <= 0 )
				{
					alert("Please enter valid points.")
				}
				else if(redeem == undefined)
				{
					alert("No Reedemption rule define")					
				}
				else{
					if(redeem.min_amt <= loyalty &&  loyalty<= redeem.max_amt)
					{
						if(parseInt(entered_code) <= loyalty)
						{
							var redeem_value = parseInt(redeem.reward_amt) * parseInt(entered_code)
							if (redeem_value > total) {
								alert('Please enter valid amount.')
							}
							if (redeem_value <= total) {
								selectedOrder.add_product(product, {
									price: -redeem_value
								});

								update_orderline_loyalty = loyalty - parseInt(entered_code)
								remove_line = orderlines.models[orderlines.length-1].id
								order.set('update_after_redeem',update_orderline_loyalty)
								update_orderline_loyalty = update_orderline_loyalty
								order.set('redeem_done', true);
								order.redeemed_points = parseInt(entered_code);
								order.set("redeem_point",parseInt(entered_code));
								self.gui.show_screen('products');
							}
						}
						else{
							alert('Please enter valid amount.')
						}
					}
					else{
						alert("limit exceeded")
					}
				}
			});

		},		
	});
	gui.define_popup({
		name: 'redeem_loyalty_popup_widget',
		widget: LoyaltyPopupWidget
	});

	// End LoyaltyPopupWidget start

	var LoyaltyButtonWidget = screens.ActionButtonWidget.extend({
		template: 'LoyaltyButtonWidget',
		button_click: function() {
			var order = this.pos.get_order();
			var self = this;
			var partner = false
			if(order.orderlines.length>0)
			{
				if(this.pos.pos_loyalty_setting.length != 0)
				{
					if (order.get_client() != null)
						partner = order.get_client();
										
					if(order.get('redeem_done')){
						self.gui.show_popup('error', {
							'title': _t('Redeem Product'),
							'body': _t('Sorry, you already added the redeem product.'),
						}); 
					}
					else if(this.pos.pos_loyalty_setting[0].redeem_ids.length == 0)
					{
						self.gui.show_popup('error', {
							'title': _t('No Redmption Rule'),
							'body': _t('Please add Redmption Rule in loyalty configuration'),
						}); 
					}
					else{
						this.gui.show_popup('redeem_loyalty_popup_widget', {'partner':partner});
					} 
				}    
			}
			else{
				self.gui.show_popup('error', {
							'title': _t('Empty Order'),
							'body': _t('Please select some products'),
				}); 
			}
			       
		},
	});

	screens.define_action_button({
		'name': 'Redeem Loyalty Points',
		'widget': LoyaltyButtonWidget,
		'condition': function() {
			return true;
		},
	});

});