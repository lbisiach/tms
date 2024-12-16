# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    service_id = fields.Many2one('service.tms', string=_("Number of Service"), required=False)

    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        for order in self:
            for invoice in order.invoice_ids:
                invoice.write({'service_id': order.service_id.id})
        return res