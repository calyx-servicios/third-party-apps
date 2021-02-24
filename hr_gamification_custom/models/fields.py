from odoo import api, fields
# from odoo import
from odoo.fields import Float
Default = object()
from odoo.sql_db import LazyCursor
from odoo.tools import float_repr, float_round
from odoo.exceptions import ValidationError

class Percent(Float):
    type = 'Percent'
    column_cast_from = ('int4', 'numeric', 'float8')
    _slots = {
        '_digits': None,
        'group_operator': 'sum',
    }

    @property
    def column_type(self):
        return ('numeric', 'numeric') if self.digits is not None else \
            ('float8', 'double precision')

    _model_name = property(fields.attrgetter('name'))
    def convert_to_column(self, value, record, values=None, validate=True):
        result = float(value or 0.0)
        digits = self.digits
        if digits:
            precision, scale = digits
            result = float_repr(float_round(result, precision_digits=scale), precision_digits=scale)
        if result < 0 or result > 100 :
            raise ValidationError("Percentage can be 0 to 100 only")

        return result

fields.Percent = Percent
