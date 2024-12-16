# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    partner_id = fields.Many2one('res.partner', string=_("Belongs to:"), domain=[('company_type','=','company'),('is_transporter','=',True)], tracking=True, ondelete="cascade")
    is_transporter = fields.Boolean(string=_("Is a Transporter"), related='partner_id.is_transporter', store=True, tracking=True)
    unit_type_id = fields.Many2one('tms.unit.type', string=_("Unit Type"), tracking=True)
    is_motorized = fields.Boolean(string=_("Is Motorized"), related='unit_type_id.is_motorized', store=True, tracking=True)
    

    @api.depends('license_plate')
    def _compute_vehicle_name(self):
        for record in self:
            record.name = ((record.license_plate + ' - ' +  record.unit_type_id.name) or _('No Plate'))
