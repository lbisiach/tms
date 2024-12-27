# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
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


    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            name = partner.with_context(lang=self.env.lang)._get_complete_name()
            if partner._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = re.sub(r'\s+\n', '\n', name)
            if partner._context.get('partner_show_db_id'):
                name = f"{name} ({partner.id})"
            if partner._context.get('address_inline'):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get('show_email') and partner.email:
                name = f"{name} <{partner.email}>"
            if partner._context.get('show_vat') and partner.vat:
                name = f"{name} ‒ {partner.vat}"
            if partner.parent_id and partner.parent_id.is_transporter:
                name = f"{partner.name}"

            partner.display_name = name.strip()