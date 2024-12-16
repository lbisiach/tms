# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TmsAddressType(models.Model):
    _name = 'tms.address.type'
    _description = _('Address Type in TMS') 
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_("Address Type"), copy=False, tracking=True, required=True)
    code = fields.Char(string=_("Code"), tracking=True)  

    def unlink(self):
        for record in self:
            if record.code == 'chofer':
                raise ValidationError(_("You cannot delete a record where the code is 'chofer'."))
        return super(TmsAddressType, self).unlink()