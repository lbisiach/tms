# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    service_id = fields.Many2one('service.tms', string=_("Number of Service"), required=False)

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_show_reset_to_draft_button(self):
        for move in self:
            move.show_reset_to_draft_button = (
                not move.restrict_mode_hash_table \
                and (move.state == 'cancel' or (move.state == 'posted' and not move.need_cancel_request))
            )
