# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TmsUnitType(models.Model):
    _name = 'tms.unit.type'
    _description = 'Unit Type in TMS'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_("Unit Type"), copy=False, tracking=True)
    is_motorized = fields.Boolean(string=_("Is Motorized"), default=False, tracking=True)
    code = fields.Char('Code', tracking=True)