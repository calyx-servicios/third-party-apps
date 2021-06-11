# -*- coding: utf-8 -*-

from odoo import models, fields, api
import fitz
import base64
import os
from odoo.exceptions import UserError
from PIL import Image, ImageDraw
import io
from io import BytesIO

class ReciboSueldo(models.Model):
    _inherit = 'hr.recibo.sueldo'

    def default_sing(self):
        output = BytesIO()    
        img = Image.new('RGB', (100, 30), color = 'white')
        d = ImageDraw.Draw(img)
        d.text((10,10),str(self.empleado_id.name), fill='black')
        img.save(output,format="JPEG")
        sing = base64.b64encode(output.getvalue())
        return sing

    @api.multi
    def sign_doc(self):
        if self.empleado_id.user_id.id != self._uid:
            raise UserError("No puede firmar el recibo de otro empleado")

        digital_signature = self.default_sing()

        recibo = base64.b64decode(self.recibo)

        docs = fitz.open("pdf", recibo)  # some existing PDF
        # page = doc[0]  # load page (0-based)
        sign_pos = self.env['config.sign'].search([('id', '=', 1)], limit=1)
        rect = fitz.Rect(int(sign_pos.sign_position_a),int(sign_pos.sign_position_b) ,int(sign_pos.sign_position_c) ,int(sign_pos.sign_position_d))  # where we want to put the image

        file_encoded = base64.b64decode(digital_signature)
        pix = fitz.Pixmap(file_encoded)

        for doc in docs:
            page = doc
            page.insertImage(rect, pixmap=pix, overlay=False)  # insert image

        namePdf = self.file_name.split('.')[0] + "_firmado.pdf"
        self.sudo().file_name_signed = namePdf
        path_store = self.env['ir.attachment']._filestore()
        file_store = path_store + "/" + namePdf
        docs.save(file_store)
        file = open(file_store, "rb")
        out = file.read()
        file.close()
        os.remove(file_store)
        gen_file = base64.b64encode(out)
        self.sudo().recibo_signed = gen_file
        self.sudo().sign_recibo = True
        return True




