odoo.define("pos_all_in_one.bi_pos_product_template", function(require){
	"use strict";
	
	var screens = require("point_of_sale.screens");
	var popups = require("point_of_sale.popups");
	var models = require('point_of_sale.models');
	var chrome = require('point_of_sale.chrome');
	var gui = require('point_of_sale.gui');
	var PosDB = require("point_of_sale.DB");
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var rpc = require('web.rpc');
	var core = require('web.core');
	var utils = require('web.utils');

	var QWeb = core.qweb;
	var _t = core._t;

	models.load_fields('product.product', ['name', 'product_template_attribute_value_ids']);


	models.load_models({
		model: 'product.template',
		fields: ['name','display_name','product_variant_ids','product_variant_count',],
		domain: [['sale_ok','=',true],['available_in_pos','=',true]],
		loaded: function(self, product_templates){
			self.product_templates = product_templates;
			self.db.add_product_templates(product_templates);
		},
	});

	PosDB.include({
		init: function(options){
			this.product_template_by_id = {};
			this._super(options);
		},
		add_product_templates: function(product_templates){
			for(var temp=0 ; temp < product_templates.length; temp++){
				var product_template_attribute_value_ids = [];
				var product_variant_ids = [];
				var qty_variants = 0;
				var prod_temp =  product_templates[temp] ; 
				this.product_template_by_id[prod_temp.id] = prod_temp;
				
				for (var prod = 0; prod < prod_temp.product_variant_ids.length; prod++){
					var product = this.product_by_id[prod_temp.product_variant_ids[prod]];
					if(product){
						qty_variants = product.product_template_attribute_value_ids.length;
						product.product_template_attribute_value_ids.forEach(function(value, index){
							product_template_attribute_value_ids.push(value);
						});
						product_variant_ids.push(product.id);
						product.product_variant_count = qty_variants;
						product.template_name = prod_temp.name
					}
				}
				const unique_attribute_value_ids = [...new Set(product_template_attribute_value_ids)]
				this.product_template_by_id[prod_temp.id].product_template_attribute_value_ids = unique_attribute_value_ids;
				this.product_template_by_id[prod_temp.id].product_variant_ids = product_variant_ids;
				if(qty_variants != 0){
					this.product_template_by_id[prod_temp.id].product_variant_count = qty_variants;
				}
			}
		},
	});
	
	screens.ProductScreenWidget.include({
		click_product: function(product) {
			if (product.product_variant_count > 1) {
				this.gui.show_popup('product_variant_popup_widget', product.product_tmpl_id);
			} else {
				this._super(product);
			}
		}
	});

	screens.ProductListWidget.include({
		set_product_list: function(product_list) {
			var self = this;
			var temp = self.pos.product_templates;
			var prods = []
			for (var i = 0; i < temp.length; i++) {
				for (var j = 0 ; j < product_list.length ; j++){
					if(product_list[j].product_tmpl_id == temp[i].id){
						var prd_list = temp[i].product_variant_ids.sort();
						prods.push(self.pos.db.get_product_by_id(prd_list[0]))
					}
				}
			}
			this._super(prods);
		},
		
		render_product: function(product){
			var self = this;

			if(product.product_variant_count > 1)
			{
				var cached = this.product_cache.get_node(product.id);
				if(!cached) {
					var image_url = this.get_product_image_url(product);
					var product_html = QWeb.render('ProductTemplate',{
							widget:  this,
							product: product,
							image_url: this.get_product_image_url(product),
						});
					var product_node = document.createElement('div');
					product_node.innerHTML = product_html;
					product_node = product_node.childNodes[1];
					this.product_cache.cache_node(product.id,product_node);
					return product_node;
				}
				return cached;
			}
			else{
				return this._super(product);
			}
		},

		check_quantity: function(prd,options) {
			var self = this;
			var product = self.pos.db.get_product_by_id(prd);
			if (product.product_variant_count > 1) {
				options.click_product_action(product);
			}
			else{
				self._super(prd,options);
			}
		},
	});
	

	var ProductTemplatePopupWidget = popups.extend({
		template:'ProductTemplatePopupWidget',

		start: function(){
			var self = this;
			this.product_template_list_widget = new ProductTemplateListWidget(this,{});
			this.product_template_list_widget.replace(this.$('.placeholder-ProductTemplateListWidget'));
		},

		show: function(product_tmpl_id){
			var self = this;
			if(this.$el){
				this.$el.removeClass('oe_hidden');
			}
			var prod_template = this.pos.db.product_template_by_id[product_tmpl_id];
			var prod_list = [];
			prod_template.product_variant_ids.forEach(function (prod) {
				prod_list.push(self.pos.db.get_product_by_id(prod));
			});
			this.product_template_list_widget.set_product_list(prod_list);
		},
	});
	gui.define_popup({
		name:'product_variant_popup_widget', 
		widget: ProductTemplatePopupWidget
	});


	var ProductTemplateListWidget = PosBaseWidget.extend({
		template:'ProductTemplateListWidget',

		init: function(parent, options) {
			var self = this;
			this._super(parent, options);
			this.product_list = [];
			this.click_product_handler = function(event){
				var product = self.pos.db.get_product_by_id(this.dataset.productId);
				if(product.to_weight && self.pos.config.iface_electronic_scale){
					self.gui.show_screen('scale',{product: product});
				}else{
					// self.pos.get_order().add_product(product);
					if(self.pos.config.pos_display_stock)
					{
						if(self.pos.config.show_stock_location == 'specific')
						{
							if (product.type == 'product')
							{
								var partner_id = self.pos.get_client();
								var location = self.pos.locations;

								rpc.query({
										model: 'stock.quant',
										method: 'get_single_product',
										args: [partner_id ? partner_id.id : 0,product.id, location],
									
									},{async : false}).then(function(output) {
										if (self.pos.config.pos_allow_order == false)
										{
											if (output[0][1] <= self.pos.config.pos_deny_order)
											{
												self.gui.show_popup('error',{
													'title': _t('Deny Order'),
													'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
												});
											}
											else if (output[0][1] <= 0)
											{
												self.gui.show_popup('error',{
													'title': _t('Error: Out of Stock'),
													'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
												});
											}
											else{
												self.pos.get_order().add_product(product);
											}
										}
										else if(self.pos.config.pos_allow_order == true)
										{
											if (output[0][1] <= self.pos.config.pos_deny_order)
											{
												self.gui.show_popup('error',{
													'title': _t('Deny Order'),
													'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
												});
											}
											else{
												self.pos.get_order().add_product(product);
											}
										}
										else{
											self.pos.get_order().add_product(product);
										}
								});
							}
							else{
								self.pos.get_order().add_product(product);
							}
						}
						else{

							if (product.type == 'product' && self.pos.config.pos_allow_order == false)
							{
							// Deny POS Order When Product is Out of Stock
								if (product.qty_available <= self.pos.config.pos_deny_order && self.pos.config.pos_allow_order == false)
								{
									self.gui.show_popup('error',{
										'title': _t('Deny Order'),
										'body': _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock.")
									});
								}
								 
								
								// Allow POS Order When Product is Out of Stock
								else if (product.qty_available <= 0 && self.pos.config.pos_allow_order == false)
								{
									self.gui.show_popup('error',{
										'title': _t('Error: Out of Stock'),
										'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
									});
								} else {
									self.pos.get_order().add_product(product);
								}
							}
							else if(product.type == 'product' && self.pos.config.pos_allow_order == true && product.qty_available <= self.pos.config.pos_deny_order){
							self.gui.show_popup('error',{
									'title': _t('Error: Out of Stock'),
									'body': _t("(" + product.display_name + ")" + " is Out of Stock."),
								});
							}	
							else if(product.type == 'product' && self.pos.config.pos_allow_order == true && product.qty_available >= self.pos.config.pos_deny_order){
								self.pos.get_order().add_product(product);
							} 
							else {
								self.pos.get_order().add_product(product);
							}
						}
					}
					else{
						self.pos.get_order().add_product(product);
					}

						}
					};
		},

		get_product_image_url: function(product){
			return window.location.origin + '/web/image?model=product.product&field=image_128&id='+product.id;
		},
		replace: function($target){
			this.renderElement();
			var target = $target[0];
			target.parentNode.replaceChild(this.el,target);
		},

		set_product_list: function(product_list){
			this.product_list = product_list;
			this.renderElement();
		},

		_get_active_pricelist: function(){
			var current_order = this.pos.get_order();
			var current_pricelist = this.pos.default_pricelist;
			if (current_order) {
				current_pricelist = current_order.pricelist;
			}
			return current_pricelist;
		},

		render_product: function(product){
			var current_pricelist = this._get_active_pricelist();
			var image_url = this.get_product_image_url(product);
			var product_html = QWeb.render('ProductProduct', {
					widget:  this,
					product: product,
					pricelist: current_pricelist,
					image_url: this.get_product_image_url(product)
				});
			var product_node = document.createElement('div');
			product_node.innerHTML = product_html;
			product_node = product_node.childNodes[1];
			return product_node;
		},

		renderElement: function() {
			var el_str  = QWeb.render(this.template, {widget: this});
			var el_node = document.createElement('div');
				el_node.innerHTML = el_str;
				el_node = el_node.childNodes[1];
			if(this.el && this.el.parentNode){
				this.el.parentNode.replaceChild(el_node,this.el);
			}
			this.el = el_node;
			var list_container = el_node.querySelector('.productt-list');
			for(var i = 0, len = this.product_list.length; i < len; i++){
				var product_node = this.render_product(this.product_list[i]);
				product_node.addEventListener('click',this.click_product_handler);
				list_container.appendChild(product_node);
			}
		},

	});	
});
