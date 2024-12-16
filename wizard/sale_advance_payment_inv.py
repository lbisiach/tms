# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            for invoice in order.invoice_ids:
                invoice.write({'service_id': order.service_id.id})
        return res