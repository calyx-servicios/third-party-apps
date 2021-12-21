# -*- coding: utf-8 -*-

import base64
from werkzeug.utils import redirect
import io
from odoo import http, _
from odoo.http import request

class AttachTechnical(http.Controller):

    @http.route(['/features_technical_download/<model(product.template):product>'], type='http', auth='public')
    def features_technical_download(self, product):
        
        term_condition = request.env['product.template'].search([('website_default','=', True), ('id', '=', product.id)])
        if term_condition:
            data = io.BytesIO(base64.standard_b64decode(term_condition.pdf_tyc))
            return http.send_file(data, filename='fichatecnica.pdf', as_attachment=False)
        else:
            return "Este producto no posee una Ficha Tecnica"