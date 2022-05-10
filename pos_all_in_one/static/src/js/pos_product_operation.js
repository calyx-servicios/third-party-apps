odoo.define('pos_all_in_one.pos_product_operation', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var rpc = require('web.rpc');
	var PosDB = require('point_of_sale.DB');

	var QWeb = core.qweb;
	var _t = core._t;

	var prd_list_count = 0;

	// Load Models here... 
	models.load_models({
		model:  'product.product',
		fields: ['display_name', 'list_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id',
				 'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description',
				 'product_tmpl_id','tracking'],
		order:  _.map(['sequence','default_code','name'], function (name) { return {name: name}; }),
		domain: function(self){
			var domain = ['&', '&', ['sale_ok','=',true],['available_in_pos','=',true],'|',['company_id','=',self.config.company_id[0]],['company_id','=',false]];
			if (self.config.limit_categories &&  self.config.iface_available_categ_ids.length) {
				domain.unshift('&');
				domain.push(['pos_categ_id', 'in', self.config.iface_available_categ_ids]);
			}
			if (self.config.iface_tipproduct){
			  domain.unshift(['id', '=', self.config.tip_product_id[0]]);
			  domain.unshift('|');
			}
			return domain;
		},
		context: function(self){ return { display_default_code: false }; },
		loaded: function(self, products){

			self.get_products = [];
			self.get_products_by_id = [];
			
			self.get_products = products;
			products.forEach(function(product) {
				self.get_products_by_id[product.id] = product;
			});
		},
	});   
		

	models.load_models({
		model:  'pos.category',
		fields: ['id','name','parent_id','child_id'],
		domain: function(self) {
			return self.config.limit_categories && self.config.iface_available_categ_ids.length ? [['id', 'in', self.config.iface_available_categ_ids]] : [];
		},
		loaded: function(self, categories){
			self.db.add_categories(categories);
			self.categories = categories;
		},
	});
	

	
	// Load PosDB
	var PosDB=PosDB.extend({
		init: function(options){
			this.product_sorted = [];
			this.product_by_id = {};
			this.product_search_string = "";
			this.product_write_date = null;
			return PosDB.prototype.init.call(this, options);
		},

		get_products_sorted: function(max_count){
			max_count = max_count ? Math.min(this.product_sorted.length, max_count) : this.product_sorted.length;
			var product = [];
			for (var i = 0; i < max_count; i++) {
				products.push(this.product_by_id[this.product_sorted[i]]);
			}
			return products;
		},

		get_product_write_date:function(products)
		{
			return this.product_write_date || "1970-01-01 00:00:00";
		},
	});


	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		load_new_products: function(){
			var self = this;
			var def  = new $.Deferred();
			var fields = _.find(this.models,function(model){ return model.model === 'product.product'; }).fields;
			var domain = _.find(this.models,function(model){ return model.model === 'product.product'; }).domain;
			return [fields ,domain]
		}    
	});
	
	// SeeAllProductsScreenWidget start

	var SeeAllProductsScreenWidget = screens.ScreenWidget.extend({
		template: 'SeeAllProductsScreenWidget',
		init: function(parent, options) {
			this._super(parent, options);
			//this.options = {};
			this.update_product = []
			this.product_list_widget = new screens.ProductListWidget(this,{});
		},
		//
		auto_back: true,
		//
		show: function() {
			
			var self = this;
			this._super();
			this.renderElement();
			this.details_visible = false;
			
			this.rerender_products();
			var products = self.update_product;
			this.render_list_products(products, undefined);
					
			this.$('.back').click(function(){
				self.gui.show_screen('products');
			});

			this.$('.new-product').click(function(){
				self.display_products_detail('edit',false);
			});

			var search_timeout = null;
			if( this.old_product ){
				this.display_products_detail('show',this.old_product,0);
			}
					
			//this code is for click on product line & that product will be appear 
			
			this.$('.products-list-contents').delegate('.products-line', 'click', function(event) {
				self.line_selects(event, $(this), parseInt($(this).data('id')));
			});

			this.$('.search-product input').on('keypress',function(event) {
				self.recreate_products_list();
				var update_products = self.update_product;
				self.render_list_products(update_products, this.value);
			});
		this.$('.searchbox .search-clear').click(function(){
			self.clear_search();
		});
			
		},
		//
		hide: function () {
			this._super();
			this.new_product = null;
		},
		rerender_products : function(){
			var self = this;
			var new_1 = self.pos.load_new_products();
			rpc.query({
				model: 'product.product',
				method: 'search_read',
				args: [new_1[1], new_1[0]],
			},{async: false})
			.then(function(output){
				self.update_product = output
				self.render_list_products(output);
				self.product_list_widget.set_new_product_list(output);
				return
			});
		},


		recreate_products_list : function(){
			var self = this;
			var new_1 = self.pos.load_new_products();
			rpc.query({
				model: 'product.product',
				method: 'search_read',
				args: [new_1[1], new_1[0]],
			},{async: false})
			.then(function(output){
				self.update_product = output
				self.product_list_widget.set_new_product_list(output);
				return
			});
		},
  

		clear_search: function(){
		var products = this.pos.get_products;;
		this.render_list_products(products);
		this.$('.searchbox input')[0].value = '';
		this.$('.searchbox input').focus();
		},

		render_list_products: function(products, search_input){
			var self = this;
			var search_products = null
			
		  if (search_input != undefined && search_input != '') {
				var selected_search_products = [];
				var search_text = search_input.toLowerCase()
				for (var i = 0; i < products.length; i++) {
					if (products[i].display_name == '') {
						products[i].display_name = [0, '-'];
					}
					if (((products[i].product_tmpl_id[1].toLowerCase()).indexOf(search_text) != -1)) { //  || ((products[i].price.toLowerCase()).indexOf(search_text) != -1) || ((products[i].pos_categ_id[1].toLowerCase()).indexOf(search_text) != -1)
						selected_search_products = selected_search_products.concat(products[i]);
					}

					if(products[i].barcode != false){
						if(products[i].barcode.indexOf(search_text) != -1){
							selected_search_products = selected_search_products.concat(products[i]);
						}
					}
				}
				products = selected_search_products;
			}
			
			var content = this.$el[0].querySelector('.products-list-contents');
			content.innerHTML = "";
			var products = products;
			for(var i = 0, len = Math.min(products.length,1000); i < len; i++){
				var product    = products[i];
				var productsline_html = QWeb.render('ProductsLine',{widget: this, product:products[i] });
				var productsline = document.createElement('tbody');
				productsline.innerHTML = productsline_html;
				productsline = productsline.childNodes[1];
				content.appendChild(productsline);

			}
		},
				 
		save_changes: function(){
			if( this.has_product_changed() ){
				this.pos.get_order().set_product(this.new_product);
			}
		},
		has_product_changed: function(){
			if( this.old_product && this.new_product ){
				return this.old_product.id !== this.new_product.id;
			}else{
				return !!this.old_product !== !!this.new_product;
			}
		},
		
		resize_image_to_dataurl: function(img, maxwidth, maxheight, callback){
			img.onload = function(){
				var canvas = document.createElement('canvas');
				var ctx    = canvas.getContext('2d');
				var ratio  = 1;

				if (img.width > maxwidth) {
					ratio = maxwidth / img.width;
				}
				if (img.height * ratio > maxheight) {
					ratio = maxheight / img.height;
				}
				var width  = Math.floor(img.width * ratio);
				var height = Math.floor(img.height * ratio);

				canvas.width  = width;
				canvas.height = height;
				ctx.drawImage(img,0,0,width,height);

				var dataurl = canvas.toDataURL();
				callback(dataurl);
			};
		},

		partner_icon_url: function(id){
		return '/web/image?model=product.product&id='+id+'&field=image_1920';
		},

		load_image_file: function(file, callback){
			var self = this;
			if (!file.type.match(/image.*/)) {
				this.gui.show_popup('error',{
					title: _t('Unsupported File Format'),
					body:  _t('Only web-compatible Image formats such as .png or .jpeg are supported'),
				});
				return;
			}
			
			var reader = new FileReader();
			reader.onload = function(event){
				var dataurl = event.target.result;
				var img     = new Image();
				img.src = dataurl;
				self.resize_image_to_dataurl(img,800,600,callback);
			};
			reader.onerror = function(){
				self.gui.show_popup('error',{
					title :_t('Could Not Read Image'),
					body  :_t('The provided file could not be read due to an unknown error'),
				});
			};
			reader.readAsDataURL(file);
		},
		
		get_selected_partner: function() {
			var self = this;
			if (self.gui)
				return self.gui.get_current_screen_param('selected_partner_id');
			else
				return undefined;
		},
		
		close: function(){
			this._super();
		},  

		toggle_save_button: function(){
			var $button = this.$('.button.next');
			if (this.editing_product) {
				$button.addClass('oe_hidden');
				return;
			} else if( this.new_product ){
				if( !this.old_product){
					$button.text(_t('Set Customer'));
				}else{
					$button.text(_t('Change Customer'));
				}
			}else{
				$button.text(_t('Deselect Customer'));
			}
			$button.toggleClass('oe_hidden',!this.has_product_changed());
		},
			
		line_selects: function(event,$line,id){
			var self = this;
			var new_1 = self.pos.load_new_products();

				rpc.query({
					model: 'product.product',
					method: 'search_read',
					args: [new_1[1], new_1[0]],
				},{async: false})
				.then(function(output){
					var products = []
					if(output){
						for(var i = 0 ; i < output.length ; i++){
							if (output[i]['id'] == id){
								products.push(output[i])
							}
						}
					}
					if(products){
						self.$('.client-list .lowlight').removeClass('lowlight');
					if ( $line.hasClass('highlight') ){
						$line.removeClass('highlight');
						$line.addClass('lowlight');
						self.display_products_detail('hide',products);
						self.new_product = null;
						self.toggle_save_button();
					}else{
						self.$('.client-list .highlight').removeClass('highlight');
						$line.addClass('highlight');
						var y = event.pageY - $line.parent().offset().top;
						self.display_products_detail('show',products,y);
						self.new_product = products;
						self.toggle_save_button();
					}
					}
				});
			
		},

		// ui handle for the 'edit selected customer' action
		edit_product_details: function(product) {
			this.display_products_detail('edit',product);
		},
	
		// ui handle for the 'cancel customer edit changes' action
		undo_product_details: function(product) {
			if (!product.id) {
				this.display_products_detail('hide');
			} else {
				this.display_products_detail('show',product);
			}
		},

		// what happens when we save the changes on the client edit form -> we fetch the fields, sanitize them,
		// send them to the backend for update, and call saved_client_details() when the server tells us the
		// save was successfull.
		save_product_details: function(product) {
			var self = this;

			var fields = {};
			this.$('.client-details-contents .detail').each(function(idx,el){
				fields[el.name] = el.value;
			});


			if (this.uploaded_picture) {
				fields.image_1920 = this.uploaded_picture;
			}

			if(fields.display_name == false){
				self.gui.show_popup('error',{
					'title': _t('Error: Could not Save Changes'),
					'body': _t('please enter product details.'),
				});
			}else{
			if (product!= false){
				fields.id           = product[0].id || false;   
			}else{
				fields.id           = false;
			}
			fields.pos_categ_id  = fields.pos_categ_id || false;
			fields.list_price      = fields.list_price || '';
			fields.standard_price      = fields.standard_price || '';
			fields.barcode      = fields.barcode || false;
			rpc.query({
					model: 'product.product',
					method: 'create_from_ui',
					args: [fields],
				})
				.then(function(product_id){
					alert('Product Details Saved!!!!')
					self.rerender_products();
					self.saved_product_details(product_id);
					self.undo_product_details(product_id);
			},function(err, event){
				self.gui.show_popup('error',{
					'title': _t('Error: Could not Save Changes'),
					'body': _t('Added Product Details getting Error.'),
				});
			});
			}
			
		},

		// what happens when we've just pushed modifications for a product of id product_id
		saved_product_details: function(product_id){
			var self = this;
				var product = self.pos.db.get_product_by_id(product_id);
				if (product) {
					self.new_product = product;
					self.toggle_save_button();
					self.display_products_detail('show',[product]);
				} else {
					// should never happen, because create_from_ui must return the id of the product it
					// has created, and reload_product() must have loaded the newly created product.
					self.display_products_detail('hide');
				}
		},


		// This fetches product changes on the server, and in case of changes,
		// rerenders the affected views
		reload_products: function(){
			var self = this;
			return this.rerender_products()
		},
		
		display_products_detail: function(visibility,product,clickpos){
			var self = this;
			var contents = this.$('.client-details-contents');
			var parent   = this.$('.products-line').parent();
			var scroll   = parent.scrollTop();
			var height   = contents.height();

			contents.off('click','.button.edit');
			contents.off('click','.button.save');
			contents.off('click','.button.undo');
			contents.on('click','.button.edit',function(){ self.edit_product_details(product); });
			contents.on('click','.button.save',function(){ self.save_product_details(product); });
			contents.on('click','.button.undo',function(){ self.undo_product_details(product); });
			this.editing_product = false;
			this.uploaded_picture = null;
		
		
			if(visibility === 'show'){
				contents.empty();
				contents.append($(QWeb.render('ProductDetails',{widget:this,product:product[0]})));

				var new_height   = contents.height();

				if(!this.details_visible){
					if(clickpos < scroll + new_height + 20 ){
						parent.scrollTop( clickpos - 20 );
					}else{
						parent.scrollTop(parent.scrollTop() + new_height);
					}
				}else{
					parent.scrollTop(parent.scrollTop() - height + new_height);
				}

				this.details_visible = true;
				this.toggle_save_button();
			} else if (visibility === 'edit') {
				this.editing_product = true;
				contents.empty();
				if(product){
				contents.append($(QWeb.render('ProductDetailsEdit',{widget:this,product:product[0],category:product[0].pos_categ_id[0]}))); 
				}else{
					contents.append($(QWeb.render('ProductDetailsEdit',{widget:this,product:false})));
				}
				this.toggle_save_button();

				contents.find('.image-uploader').on('change',function(event){
					self.load_image_file(event.target.files[0],function(res){
						if (res) {
							contents.find('.client-picture img, .client-picture .fa').remove();
							contents.find('.client-picture').append("<img src='"+res+"'>");
							contents.find('.detail.picture').remove();
							self.uploaded_picture = res;
						}
					});
				});
			} 
			else if (visibility === 'hide') {
				contents.empty();
				if( height > scroll ){
					contents.css({height:height+'px'});
					contents.animate({height:0},400,function(){
						contents.css({height:''});
					});
				}else{
					parent.scrollTop( parent.scrollTop() - height);
				}
				this.details_visible = false;
				this.toggle_save_button();
			}
		},
		
		get_selected_partner: function() {
			var self = this;
			if (self.gui)
				return self.gui.get_current_screen_param('selected_partner_id');
			else
				return undefined;
		},
		
		close: function(){
			this._super();
		},        
		
	});
	gui.define_screen({
		name: 'see_all_products_screen_widget',
		widget: SeeAllProductsScreenWidget
	});

	// End SeeAllProductsScreenWidget
	
	// Start SeeAllProductsButtonWidget
	var SeeAllProductsButtonWidget = screens.ActionButtonWidget.extend({
		template: 'SeeAllProductsButtonWidget',
		button_click: function() {
			var self = this;
			this.gui.show_screen('see_all_products_screen_widget', {});
		},
		
	});

	screens.define_action_button({
		'name': 'See All Products Button Widget',
		'widget': SeeAllProductsButtonWidget,
		'condition': function() {
			return true;
		},
	});
	
	screens.ProductListWidget.include({

		init: function(parent, options) {
			var self = this;
			this._super(parent,options);
			this.new_products = self.pos.get_products || [];
		},

		set_new_product_list: function(product_list){
			this.new_products = product_list;
			this.renderElement();
		},

		renderElement: function() {
			var self = this;
			var new_products_list = [];
			if(self.pos.get_products > 0){
				for(var i = 0, len = this.new_products.length; i < len; i++){
					new_products_list.push(self.pos.db.get_product_by_id(this.new_products[i]))
				}
			}else{
				new_products_list = this.product_list;
			}
			
			var el_str  = QWeb.render(this.template, {widget: this});
			var el_node = document.createElement('div');
				el_node.innerHTML = el_str;
				el_node = el_node.childNodes[1];
			if(this.el && this.el.parentNode){
				this.el.parentNode.replaceChild(el_node,this.el);
			}
			this.el = el_node;
			var list_container = el_node.querySelector('.product-list');

			if (self.pos.config.show_stock_location == 'specific')
			{
				var x_sync = this.pos.get("is_sync")
				var location = self.pos.locations;
				if(x_sync == true){
					if (self.pos.config.pos_stock_type == 'onhand')
					{
						rpc.query({
								model: 'stock.quant',
								method: 'get_stock_location_qty',
								args: [1, location],
							
							},{async : false}).then(function(output) {
								self.pos.loc_onhand = output[0];
								for(var i = 0, len = new_products_list.length; i < len; i++){
									new_products_list[i]['bi_on_hand'] = new_products_list[i].qty_available;
									new_products_list[i]['bi_available'] = new_products_list[i].virtual_available;

									for(let key in self.pos.loc_onhand)
									{
										if(new_products_list[i].id == key)
										{
											new_products_list[i]['bi_on_hand'] = self.pos.loc_onhand[key];

											var product_qty_final = $("[data-product-id='"+new_products_list[i].id+"'] #stockqty");
											product_qty_final.html(self.pos.loc_onhand[key])
											var product_qty_avail = $("[data-product-id='"+new_products_list[i].id+"'] #availqty");
											product_qty_avail.html(new_products_list[i].virtual_available);
										}
									}
									var product_node = self.render_product(new_products_list[i]);
									product_node.addEventListener('click',self.click_product_handler);
									product_node.addEventListener('keypress',self.keypress_product_handler);
									list_container.appendChild(product_node);
								}
								self.pos.set("is_sync",false);
						});
					}
					if (self.pos.config.pos_stock_type == 'available')
					{
						rpc.query({
								model: 'product.product',
								method: 'get_stock_location_avail_qty',
								args: [1, location],
							
						},{async : false}).then(function(output) {
								
							self.pos.loc_available = output[0];
							for(var i = 0, len = new_products_list.length; i < len; i++){
								new_products_list[i]['bi_on_hand'] = new_products_list[i].qty_available;
								new_products_list[i]['bi_available'] = new_products_list[i].virtual_available;

								for(let key in self.pos.loc_available)
								{
									if(new_products_list[i].id == key)
									{
										new_products_list[i]['bi_available'] = self.pos.loc_available[key];
										var product_qty_final = $("[data-product-id='"+new_products_list[i].id+"'] #stockqty");
										product_qty_final.html(new_products_list[i].qty_available)
										var product_qty_avail = $("[data-product-id='"+new_products_list[i].id+"'] #availqty");
										product_qty_avail.html(self.pos.loc_available[key]);
									}
								}
								var product_node = self.render_product(new_products_list[i]);
								product_node.addEventListener('click',self.click_product_handler);
								product_node.addEventListener('keypress',self.keypress_product_handler);
								list_container.appendChild(product_node);
							}
							self.pos.set("is_sync",false);
						});
					}
				}else{
					for(var i = 0, len = new_products_list.length; i < len; i++){
						var product_node = this.render_product(new_products_list[i]);
						product_node.addEventListener('click',this.click_product_handler);
						product_node.addEventListener('keypress',this.keypress_product_handler);
						list_container.appendChild(product_node);
					}
				}
			}
			else{
				for(var i = 0, len = new_products_list.length; i < len; i++){
					new_products_list[i]['bi_on_hand'] = new_products_list[i].qty_available;
					new_products_list[i]['bi_available'] = new_products_list[i].virtual_available;
					var product_node = this.render_product(new_products_list[i]);
					product_node.addEventListener('click',this.click_product_handler);
					product_node.addEventListener('keypress',this.keypress_product_handler);
					list_container.appendChild(product_node);
				}
			}
			prd_list_count += 1;
			if(prd_list_count > 0){
				self.pos.set("is_sync",false);
			}

		},

	});	

});