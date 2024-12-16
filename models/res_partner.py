# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_transporter = fields.Boolean(string=_("Is a Transporter"), default=False, tracking=True)
    fleet_ids = fields.Many2many('fleet.vehicle', string=_("Fleet"), domain="[('company_id', '=', company_id)]", 
                                 tracking=True, help=_("Vehicles owned by this partner"), compute="_compute_fleet_ids")
    tms_address_type_ids = fields.Many2many('tms.address.type', string=_("Address Types"), tracking=True)
    driver_ids = fields.Many2many(
        'res.partner',
        'res_partner_driver_rel',
        'partner_id',
        'driver_id',
        string=_("Drivers"),
        compute="_compute_driver_ids",
        domain="[('tms_address_type_ids.code', '=', 'chofer'), ('company_id', '=', company_id)]", 
        help=_("Drivers associated with this partner"),
        tracking=True
    )

    def _compute_fleet_ids(self):
        for partner in self:
            partner.fleet_ids = self.env['fleet.vehicle'].search([
                ('partner_id', '=', partner.id),
                ('company_id', '=', partner.company_id.id)
            ])

    def _compute_driver_ids(self):
        for partner in self:
            drivers = self.env['res.partner'].search([
                ('tms_address_type_ids.code', '=', 'chofer'),
                ('company_id', '=', partner.company_id.id)
            ])
            partner.driver_ids = drivers