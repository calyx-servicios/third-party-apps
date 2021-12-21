# -*- coding: utf-8 -*-

import base64
from werkzeug.utils import redirect
import io
from odoo import http
from odoo.http import request

class AttachTechnical(http.Controller):

    @http.route(['/features_technical_download'], type='http', auth='public')
    def features_technical_download(self):
        
        term_condition = request.env['product.template'].search([('website_default','=', True),('id','=', self.id)])
        data = io.BytesIO(base64.standard_b64decode(term_condition.pdf_tyc))
        return http.send_file(data, filename='fichatecnica.pdf', as_attachment=False)