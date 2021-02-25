# -*- coding: utf-8 -*-
import odoo.http as http
from odoo import _
from odoo.http import request
from datetime import datetime


class ProductApi(http.Controller):
    def _get_categ_ids(self, name):
        categ_ids = []
        product_categ_obj = request.env["product.category"].search(
            [
                ("name", "ilike", name),
            ],
        )
        for category in product_categ_obj:
            categ_ids.append(product_categ_obj.id)
        return categ_ids

    def _get_pos_categ_ids(self, name):
        categ_ids = []
        product_pos_categ_obj = request.env["pos.category"].search(
            [
                ("name", "ilike", name),
            ],
        )
        for category in product_pos_categ_obj:
            categ_ids.append(product_pos_categ_obj.id)
        return categ_ids

    def _get_values_ids(self, name):
        value_ids = []
        product_value_obj = request.env[
            "product.attribute.value"
        ].search(
            [
                ("name", "ilike", name),
            ],
        )
        for value in product_value_obj:
            value_ids.append(product_value_obj.id)

        return value_ids

    @http.route(
        "/get_products", auth="user", type="json", method=["GET"]
    )
    def get_products(self, **kw):
        message = None
        products = []
        domain = []

        categ_id_name = kw.get("categ", False)
        values_id_name = kw.get("values", False)
        product_name = kw.get("product", False)
        pos_categ_name = kw.get("pos_categ", False)

        if (
            not categ_id_name
            and not values_id_name
            and not product_name
            and not pos_categ_name
        ):
            message = _("You have to set al leats one parameter.")
            data = {"status": 400, "message": message}

        else:

            if product_name:
                domain += [
                    ("name", "ilike", product_name),
                ]

            if categ_id_name:
                product_categ_ids = self._get_categ_ids(categ_id_name)
                if product_categ_ids:
                    domain += [
                        ("categ_id", "in", product_categ_ids),
                    ]

            if pos_categ_name:
                product_pos_categ_ids = self._get_pos_categ_ids(
                    pos_categ_name
                )
                if product_pos_categ_ids:
                    domain += [
                        ("pos_categ_id", "in", product_pos_categ_ids),
                    ]

            if values_id_name:
                product_value_ids = self._get_values_ids(values_id_name)
                if product_value_ids:
                    domain += [
                        (
                            "attribute_value_ids",
                            "in",
                            product_value_ids,
                        ),
                    ]

            product_obj = request.env["product.product"].search(domain)

            for product in product_obj:
                attributes = {}

                for value in product.attribute_value_ids:
                    attributes[value.attribute_id.name] = value.name

                data = {
                    "category": product.categ_id.name,
                    "default_code": product.default_code,
                    "name": product.name,
                    "sale_price": product.lst_price,
                    "cost_price": product.standard_price,
                    "qty_available": product.qty_available,
                    "qty_virtual": product.virtual_available,
                    "attributes": attributes,
                }
                products.append(data)

                data = {
                    "status": 200,
                    "response": products,
                    "message": "Sucess",
                }

        return data
