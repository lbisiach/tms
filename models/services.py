# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process,api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)
    

class ServiceTms(models.Model):
    _name = 'service.tms'
    _description = _('Services of Transport Manager System') 
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_("N° of Service"), copy=False, readonly=True, tracking=True) 
    label_service = fields.Char(string=_("Material/Reference"), required=True, tracking=True)
    date_start = fields.Date(string=_("Date Start"), default=fields.Datetime.now, required=True, tracking=True)
    date_stop = fields.Date(string=_("Date End"), default=fields.Datetime.now, required=True, tracking=True)
    state = fields.Selection([
        ('draft',_('New')),
        ('in_process',_('In Process')),
        ('finalized',_('Finalized')),
        ('invoiced',_('Invoiced'))], string=_("State"), default="draft", tracking=True)
    notes = fields.Html(string=_("Notes"), tracking=True)
    customer_notes = fields.Html(string=_("Customer Notes"), tracking=True)
    supplier_notes = fields.Html(string=_("Supplier Notes"), tracking=True)
    customer_ids = fields.One2many('service.tms.supplier.customer.line', 'sale_service_id', string=_("Customer"), tracking=True)
    supplier_ids = fields.One2many('service.tms.supplier.customer.line', 'purchase_service_id', string=_("Supplier"), tracking=True)
    fleet_ids = fields.One2many('service.tms.fleet.line', 'service_id', string=_("Fleet"), tracking=True)
    own_third_freight = fields.Boolean(default=False, string=_("Third Freight"), help=_("The freight is third if this fields is checked."))
    attachment_ids = fields.Many2many('ir.attachment', string=_("Attachments"), tracking=True)
    service_line_ids = fields.One2many('service.tms.line', 'service_id', string=_("Service Lines"), tracking=True)
    distance = fields.Integer(string=_("Distance"), compute='_compute_distance', store=True)
    distance_uploaded = fields.Integer(string=_("Distance Uploaded"), compute="_compute_distance", default=False, store=True)
    distance_empty = fields.Integer(string=_("Distance Empty"), compute="_compute_distance", default=False, store=True)
    tn_loaded = fields.Float(string=_("Tn Loaded"), default=0, tracking=True)
    tn_downloaded = fields.Float(string=_("Tn Downloaded"), default=0, tracking=True)
    tn_depletion = fields.Float(string=_("Tn Depletion"), default=0, tracking=True, compute="_compute_tn_depletion", store=True)
    tn_gauging = fields.Float(string=_("Tn Gauging"), default=0, tracking=True)
    tn_net = fields.Float(string=_("Tn Net"), default=0, tracking=True, compute="_compute_tn_net", store=True)
    billing_type = fields.Selection([
        ('unit', _("By Unit")),
        ('distance', _("By Distance")),
        ('ton', _("By Tn"))], string=_("Invoicing Method"), default='unit', required=True, tracking=True, store=True)
    show_hour = fields.Boolean(string=_("Show Hour"), default=False)
    sale_order_ids = fields.One2many('sale.order', 'service_id', string=_("Sale Orders"))
    sale_order_count = fields.Integer(string="Sale Order Count", compute="_compute_sale_order_count")
    invoice_sale_count = fields.Integer(string="Invoice Sale Count", compute="_compute_invoice_sale_count")
    invoice_purchase_count = fields.Integer(string="Invoice Purchase Count", compute="_compute_invoice_purchase_count")
    hide_sale_order = fields.Boolean(string=_("Show Sale Order"), default=False, compute="_compute_show_sale_order")
    hide_purchase_order = fields.Boolean(string=_("Show Purchase Order"), default=False, compute="_compute_show_purchase_order")
    purchase_order_ids = fields.One2many('purchase.order', 'service_id', string=_("Purchase Orders"))
    purchase_order_count = fields.Integer(string="Purchase Order Count", compute="_compute_purchase_order_count")
    customer_invoice_ids = fields.One2many('account.move', 'service_id', string=_("Customer Invoices"))
    supplier_invoice_ids = fields.One2many('account.move', 'service_id', string=_("Supplier Invoices"))

    _sql_constraints = [
        ('unique_service_name', 'UNIQUE(name)', 'The service name must be unique.')
    ]

    def button_in_process(self):
        self.state = 'in_process'

    def button_finalized(self):
        self.state = 'finalized'
    
    def button_draft(self):
        self.state = 'draft'

    def button_invoiced(self):
        self.state = 'invoiced'

    def _compute_invoice_sale_count(self):
        for record in self:
            record.invoice_sale_count = 0
            for sale in record.sale_order_ids:
                record.invoice_sale_count = len(sale.invoice_ids)

    def _compute_invoice_purchase_count(self):
        for record in self:
            record.invoice_purchase_count = 0
            for purchase in record.purchase_order_ids:
                record.invoice_purchase_count = len(purchase.invoice_ids)

    @api.depends('sale_order_ids')
    def _compute_show_sale_order(self):
        for rec in self:
            total_orders = len(rec.customer_ids)
            orders_with_sale_order_id = len(rec.customer_ids.filtered(lambda order: order.sale_order_id))
            if total_orders == orders_with_sale_order_id:
                rec.hide_sale_order = True
            else:
                rec.hide_sale_order = False
    
    @api.depends('purchase_order_ids')
    def _compute_show_purchase_order(self):
        for rec in self:
            total_orders = len(rec.supplier_ids)
            orders_with_purchase_order_id = len(rec.supplier_ids.filtered(lambda order: order.purchase_order_id))
            if total_orders == orders_with_purchase_order_id:
                rec.hide_purchase_order = True
            else:
                rec.hide_purchase_order = False

    def create_sales_order(self):
        if not self.customer_ids:
            raise ValidationError(_("You must add at least one customer line."))

        # Filtrar líneas que no tienen un sale_order_id asociado
        lines_to_process = self.customer_ids.filtered(lambda line: not line.sale_order_id)

        if not lines_to_process:
            return  # Si todas las líneas tienen órdenes de venta, no hacemos nada

        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        # Agrupar líneas por cliente y moneda
        orders_data = {}
        for line in lines_to_process:
            key = (line.customer_id.id, line.currency_id.id)
            if key not in orders_data:
                orders_data[key] = []
            orders_data[key].append(line)

        # Crear pedidos de venta por cada grupo
        for (customer_id, currency_id), lines in orders_data.items():
            # Crear el pedido básico
            service_id = lines[0].sale_service_id
            sale_order = SaleOrder.create({
                'partner_id': customer_id,
                'currency_id': currency_id,
            })

            for line in lines:
                # Crear la línea de pedido de venta
                sale_order_line = SaleOrderLine.create({
                    'order_id': sale_order.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'name': line.product_id.name,
                })

                # Asociar la línea de customer_ids con el sale.order y sale.order.line
                line.sale_order_id = sale_order.id
                line.sale_order_line_id = sale_order_line.id
            sale_order.service_id = service_id

    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = len(record.sale_order_ids)

    def action_view_sales_orders(self):
        self.ensure_one() 
        action = self.env.ref('sale.action_orders').read()[0]  
        action['domain'] = [('id', 'in', self.sale_order_ids.ids)] 
        return action
    
    def action_view_customer_invoices(self):
        self.ensure_one() 
        action = self.env['account.move'].search([('service_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', action.ids)],
        }
    
    def create_purchase_order(self):
        if not self.supplier_ids:
            raise ValidationError(_("You must add at least one supplier line."))

        # Filtrar líneas que no tienen un purchase_order_id asociado
        lines_to_process = self.supplier_ids.filtered(lambda line: not line.purchase_order_id)

        if not lines_to_process:
            return  # Si todas las líneas tienen órdenes de venta, no hacemos nada

        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        # Agrupar líneas por cliente y moneda
        orders_data = {}
        for line in lines_to_process:
            key = (line.supplier_id.id, line.currency_id.id)
            if key not in orders_data:
                orders_data[key] = []
            orders_data[key].append(line)

        # Crear pedidos de venta por cada grupo
        for (supplier_id, currency_id), lines in orders_data.items():
            # Crear el pedido básico
            service_id = lines[0].purchase_service_id
            purchase_order = PurchaseOrder.create({
                'partner_id': supplier_id,
                'currency_id': currency_id,
            })

            for line in lines:
                # Crear la línea de pedido de venta
                purchase_order_line = PurchaseOrderLine.create({
                    'order_id': purchase_order.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'name': line.product_id.name,
                    'discount': line.discount,
                })

                # Asociar la línea de supplier_ids con el purchase.order y purchase.order.line
                line.purchase_order_id = purchase_order.id
                line.purchase_order_line_id = purchase_order_line.id

            purchase_order.service_id = service_id

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one() 
        action = self.env.ref('purchase.purchase_rfq').read()[0]  
        action['domain'] = [('id', 'in', self.purchase_order_ids.ids)] 
        return action

    def action_view_purchase_invoices(self):
        self.ensure_one() 
        action = self.env['account.move'].search([('service_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Supplier Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', action.ids)],
        }


    @api.onchange('customer_ids')
    def _onchange_customer_ids(self):
        for record in self:
            for line in record.customer_ids:
                line.billing_type = record.billing_type

    @api.depends('tn_loaded', 'tn_downloaded')
    def _compute_tn_depletion(self):
        for record in self:
            if record.tn_downloaded > record.tn_loaded:
                raise ValidationError(_("The downloaded Tn cannot be greater than the loaded Tn."))
            record.tn_depletion = record.tn_loaded - record.tn_downloaded
    
    @api.depends('tn_downloaded', 'tn_gauging')
    def _compute_tn_net(self):
        for record in self:
            record.tn_net = max(record.tn_downloaded, record.tn_gauging)

    #Create sequence of services.
    @api.model
    def create(self,vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('service.tms') or _('New') + ' '
        res = super(ServiceTms, self).create(vals)
        return res
    
    @api.depends('service_line_ids')
    def _compute_distance(self):
        for record in self:
            record.distance = sum(line.distance for line in record.service_line_ids)
            record.distance_empty = sum(line.distance for line in record.service_line_ids if not line.uploaded)
            record.distance_uploaded = sum(line.distance for line in record.service_line_ids if line.uploaded)
            

class ServiceTmsLine(models.Model):
    _name = 'service.tms.line'
    _description = _('Lines of Services of Transport Manager System')
    _inherit = ['mail.thread', 'mail.activity.mixin']

    service_id = fields.Many2one('service.tms', string=_("Service"), ondelete='cascade')
    date_start = fields.Date(string=_("Date Start"), default=fields.Datetime.now, required=True)
    hour_start = fields.Float(string=_("Hour Start"))
    date_end = fields.Date(string=_("Date End"), default=fields.Datetime.now, required=True)
    hour_end = fields.Float(string=_("Hour End"))
    place_start = fields.Char(string=_("Start Place"), required=True)
    url_place_start = fields.Char(string=_("URL Start Place"))
    place_end = fields.Char(string=_("End Place"))
    url_place_end = fields.Char(string=_("URL End Place"))
    uploaded = fields.Boolean(string=_("Uploaded"), default=False)
    distance = fields.Integer(string=_("Distance"))
    note = fields.Char(string=_("Note"))

class ServiceTmsFleetLine(models.Model):
    _name = 'service.tms.fleet.line'
    _description = _('Fleet of Services of Transport Manager System')
    _rec_name = 'fleet_vehicle_id'

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string=_("Fleet Vehicle"),
                                               domain=lambda self: self._get_fleet_vehicle_domain(is_motorized=True))
    fleet_vehicle_trailer_id = fields.Many2one('fleet.vehicle', string=_("Fleet Vehicle"), 
                                                       domain=lambda self: self._get_fleet_vehicle_domain(is_motorized=False))
    driver_id = fields.Many2one('res.partner', string=_("Driver"))
    partner_id = fields.Many2one('res.partner', string=_("Partner"), required=True, domain=[('company_type','=','company'),('is_transporter','=',True),('parent_id','=',False)])
    service_id = fields.Many2one('service.tms', string=_("Service"), ondelete='cascade')
    note = fields.Char(string=_("Note"))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.fleet_vehicle_id = False
        self.fleet_vehicle_trailer_id = False

    def _get_fleet_vehicle_domain(self, is_motorized):
        domain = [('is_motorized', '=', is_motorized)]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        return domain
    
class ServiceTmsCustomerLine(models.Model):
    _name = 'service.tms.supplier.customer.line'
    _description = _('Supplier of Services of Transport Manager System')

    customer_id = fields.Many2one('res.partner', string=_("Customer"), domain=[('customer_rank','>',0),('company_type','=','company'),('parent_id','=',False)])
    supplier_id = fields.Many2one('res.partner', string=_("Supplier"), domain=[('supplier_rank','>',0),('company_type','=','company'),('parent_id','=',False)])
    operation_type = fields.Selection([('sale', _("Sale")), ('purchase', _("Purchase"))], string=_("Type of Operation"), required=True)
    product_id = fields.Many2one('product.product', string=_("Product"), required=True, domain=[('tms_product','=',True)], context={'default_tms_product': True, 'default_detailed_type': 'service'})
    quantity = fields.Float(string=_("Quantity"), required=True, default=0)
    currency_id = fields.Many2one('res.currency', string=_("Currency"), required=True, default=lambda self: self.env.company.currency_id.id)
    price_unit = fields.Monetary(string=_("Price Unit"), required=True)
    purchase_service_id = fields.Many2one('service.tms', string=_("Service"), ondelete='cascade')
    sale_service_id = fields.Many2one('service.tms', string=_("Service"), ondelete='cascade')
    billing_type = fields.Selection([
        ('unit', _("By Unit")),
        ('distance', _("By Distance")),
        ('ton', _("By Tn"))], string=_("Invoicing Method"), default='unit', required=True, tracking=True, store=True)
    discount = fields.Float(string=_("Discount"), default=0)
    amount = fields.Monetary(string=_("Amount Total"), compute='_compute_amount', store=True)

    sale_order_id = fields.Many2one('sale.order', string=_("Sale Order"), ondelete='set null')
    sale_order_line_id = fields.Many2one('sale.order.line', string=_("Sale Order Line"), ondelete='set null')
    sale_order_state = fields.Selection(related='sale_order_id.state', string=_("Sale Order State"))

    purchase_order_id = fields.Many2one('purchase.order', string=_("Purchase Order"), ondelete='set null')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string=_("Purchase Order Line"), ondelete='set null')
    purchase_order_state = fields.Selection(related='purchase_order_id.state', string=_("Purchase Order State"))

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_amount(self):
        for record in self:
            discount_factor = 1 - record.discount if record.discount else 1
            record.amount = record.quantity * record.price_unit * discount_factor