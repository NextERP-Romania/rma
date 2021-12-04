from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaGroup(models.Model):
    _name = "rma.group"
    _description = "RMA Group"
    _order = "date desc"
    _inherit = ["mail.thread", "portal.mixin", "mail.activity.mixin"]

    def create(self, vals):
        
            if type(vals) is list:
                vals = vals[0]
            if "order_id" in vals:
                latest_rma = self.search_read(
                    [("order_id", "=", vals["order_id"])],
                    ["name"],
                    order="id desc",
                    limit=1,)
                if latest_rma:
                    orginal_name = str(latest_rma[0]["name"])
                    nr_position = orginal_name.rfind("#")
                    if nr_position >= 0:
                        name = orginal_name[:nr_position+1] + str(
                            int(orginal_name[nr_position+1:]) + 1 )
                    else:
                        name = orginal_name + "#1"
                else:
                    name =  "RMA_"+self.env["sale.order"].browse(vals["order_id"]).name
                vals["name"] = name
            else:
                raise ValidationError("You can not create a RMA_group that does not have a order_id")
                
            res_ids = super(RmaGroup,self).create(vals)   
            return res_ids

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order", readonly=1
    )
    company_id = fields.Many2one(comodel_name="res.company", related="order_id.company_id", store=1, readonly=1)

    count_invoices = fields.Integer(compute="_compute_group_state")
    count_outgoing_transfers = fields.Integer(compute="_compute_group_state")
    count_incomming_tranfers = fields.Integer(compute="_compute_group_state")

    #    original_transfers = = fields.One2many('stock.picking',compute="_compute_group_state")
    invoices_ids = fields.One2many(
        "account.move", "rma_group_id", compute="_compute_group_state"
    )
    outgoing_transfers_ids = fields.One2many(
        "stock.picking", "rma_group_id", compute="_compute_group_state"
    )
    incomming_tranfers_ids = fields.One2many(
        "stock.picking", "rma_group_id", compute="_compute_group_state"
    )

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/rmags/{}".format(record.id)

    def write(self, values):
        if "order_id" in values:
            raise ValidationError("You can not change a order_id of a rma_group")
        return super().write(values)

    sent = fields.Boolean()
    name = fields.Char(string="Name", readonly=1, store=True)
    date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        index=True,
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        index=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="order_id.company_id",
        readonly=1,
    )
    partner_id = fields.Many2one(
        string="Customer",
        readonly=1,
        comodel_name="res.partner",
        related="order_id.partner_id",
        store=1,
    )
    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner",
        readonly=1,
        related="partner_id.commercial_partner_id",
    )
    #    b2b = fields.Selection(readonly=1,related="partner_id.b2b")
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        readonly=1,
        related="partner_id.property_product_pricelist",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("received", "Received"),
            ("mixt", "mixt"),
            #                 ("waiting_return", "Waiting for return"),
            #                 ("waiting_replacement", "Waiting for replacement"),
            #                 ("locked", "Locked"),
            ("resolved", "Resolved"),
            #                 ("refunded", "Refunded"),
            #                 ("returned", "Returned"),
            #                 ("replaced", "Replaced"),
            ("cancelled", "Cancelled"),
        ],
        store="1",
        compute="_compute_group_state",
    )
    rma_ids = fields.One2many("rma", "rma_group_id")
    finised = fields.Boolean(
        help="if this is true, means that we do not need to do anything with this group"
    )

    can_be_replaced = fields.Boolean(compute="_compute_group_state", store=1)
    can_be_refunded = fields.Boolean(compute="_compute_group_state", store=1)

    @api.depends("rma_ids", "rma_ids.state")
    def _compute_group_state(self):
        for rec in self:
            states = [x.state for x in rec.rma_ids]
            if not states:
                state = "draft"
            elif all([x == "draft" for x in states]):
                state = "draft"
            elif all([x == "received" for x in states]):
                state = "received"
            elif all([x == "confirmed" for x in states]):
                state = "confirmed"
            elif all([x == "cancelled" for x in states]):
                state = "cancelled"
            elif all([x in ["refunded", "returned", "replaced"] for x in states]):
                state = "resolved"
            else:
                state = "mixt"
            rec.state = state
            if state not in ["draft", "cancelled", "resolved"]:
                if rec.rma_ids.filtered(lambda r: r.operation_id.name == "Replace" and r.state!="replaced"):
                    rec.can_be_replaced = 1
                else:
                    rec.can_be_replaced = 0
                if rec.rma_ids.filtered(lambda r: r.operation_id.name == "Refund" and r.state!="refunded"):
                    rec.can_be_refunded = 1
                else:
                    rec.can_be_refunded = 0
            invoices_ids, outgoing_transfers_ids, incomming_tranfers_ids = [], [], []
            for rma in self.rma_ids:
                invoices_ids.extend([rma.refund_id.id] if rma.refund_id else [])
                incomming_tranfers_ids.extend(
                    [rma.reception_move_id.picking_id.id]
                    if rma.reception_move_id
                    else []
                )
                outgoing_transfers_ids.extend(
                    [x.picking_id.id for x in rma.delivery_move_ids]
                )
            rec.invoices_ids = [(6, 0, set(invoices_ids))]
            rec.count_invoices = len(set(invoices_ids))
            rec.outgoing_transfers_ids = [(6, 0, set(outgoing_transfers_ids))]
            rec.count_outgoing_transfers = len(set(outgoing_transfers_ids))
            rec.incomming_tranfers_ids = [(6, 0, set(incomming_tranfers_ids))]
            rec.count_incomming_tranfers = len(set(incomming_tranfers_ids))
 
    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        """Set 'sent' field to True when an email is sent from rma form
        view. This field (sent) is used to set the appropriate style to the
        'Send by Email' button in the rma form view.
        """
        if self.env.context.get("mark_rma_as_sent"):
            self.write({"sent": True})
        # mail_post_autofollow=True to include email recipient contacts as
        # RMA followers
        self_with_context = self.with_context(mail_post_autofollow=True)
        return super(RmaGroup, self_with_context).message_post(**kwargs)
 
    # Action methods
    def action_rma_send(self):
        self.ensure_one()
        template = self.env.ref("rma_group.mail_template_rma_group_notification", False)
        form = self.env.ref("mail.email_compose_message_wizard_form", False)
        ctx = {
            "default_model": "rma",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template),
            "default_template_id": template and template.id or False,
            "default_composition_mode": "comment",
            "mark_rma_as_sent": True,
            "model_description": "RMA_GROUP",
            "force_email": True,
        }
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(form.id, "form")],
            "view_id": form.id,
            "target": "new",
            "context": ctx,
        }

    def action_confirm(self):
        """Invoked when 'Confirm' button in rma form view is clicked.
        will call the _create_reception_from_picking and _from_product  in rma
        """
        self.ensure_one()
        if not self.state == "draft" and not self.rma_ids:
            raise ValidationError(
                "You can not create reception when state is not draft OR you can not create receptions if you do not have RMA lines"
            )

        pickings = {}
        for rma in self.rma_ids:
            if rma.picking_id.id not in pickings:
                pickings[rma.picking_id.id] = [rma]
            else:
                pickings[rma.picking_id.id].append(rma)
        for key in pickings:
            create_vals = {
                "location_id": pickings[key][0].location_id.id,
                "picking_id": pickings[key][0].picking_id.id,
            }
            return_wizard = (
                self.env["stock.return.picking"]
                .with_context(active_id=key, active_ids=[key])
                .create(create_vals)
            )
            return_wizard._onchange_picking_id()  # is creating all the lines from picking
            for return_move in return_wizard.product_return_moves:
                move_id = return_move.move_id     # here can be a error when you create without a product
                rma = [x for x in pickings[key] if x.move_id == move_id]
                if not rma:
                    return_move.unlink()  # this line is not in RMA to return
                else:
                    return_move.quantity = rma[0].product_uom_qty

            # set_rma_picking_type is to override the copy() method of stock
            # picking and change the default picking type to rma picking type.
            picking_action = return_wizard.with_context(
                set_rma_picking_type=True
            ).create_returns()
            picking_id = picking_action["res_id"]
            print(f"created returned picking={picking_id}")
            picking = self.env["stock.picking"].browse(picking_id)
            picking.write({'origin': "{} ({})".format(self.name, picking.origin),'rma_group_id':self.id   })
            for rma in pickings[key]:
                rma.write(
                    {
                        "reception_move_id": [
                            x.id
                            for x in picking.move_lines
                            if x.product_id == rma.product_id
                        ][0],
                        "state": "confirmed",
                    }
                )
                if rma.partner_id not in self.message_partner_ids:
                    rma.message_subscribe([self.partner_id.id])
        return

    def action_refund(self,called_from_sale_order_create_invoice=False,super_create_invoices=False): 
        """will press the button "create invoice" from sale order to invoice 
          is a problem if you press in sale order this button becuse is not going to record the inovice in this rma
          when called with parameter called_from_sale_order_create_invoice means that is called from _create_invoices from sale order and will call the super ( otherwise will be a loop)
        """
        self.ensure_one()
        refund_lines = self.rma_ids.filtered(lambda r: r.state == "received" and r.operation_id.name=="Refund")
        product_dict = {x.product_id.id:x for x in refund_lines}
        if  not refund_lines:
            raise ValidationError("Is no line that has state=='received' and operation_id.name=='Refund'")
        if called_from_sale_order_create_invoice:
            invoice = super_create_invoices(final=True)
        else:
            invoice = self.order_id._create_invoices(final=True,from_action_refund=True)  # new created invoice for return
        if invoice.move_type != 'out_refund':
            raise ValidationError(f"The return invoice must be type 'out_refund' but is {invoice.move_type}")
        invoice_lines = {}  # dictionay with key  line of invoice and value the rma object ( rma not rma_group)
        for line in invoice.invoice_line_ids:
            if line.product_id.id not in product_dict:
                line.unlink()
            elif line.quantity != product_dict[line.product_id.id].product_uom_qty:
                raise  ValidationError(f"for line with product_id={line.product_id.name} the return invoice qty={line.quantity} but RMA qty ={product_dict[line.product_id.id].product_uom_qty}")
            else:
                invoice_lines[line.id] = product_dict[line.product_id.id]
                line.rma_id = product_dict[line.product_id.id].id
        if  len(invoice_lines) != len(product_dict):
            raise ValidationError(f"Some lines are not in return invoice. please do it manually.\nIn Invoice:{[x.product_id.name for x in invoice.invoice_line_ids]}\nIn RMA:{[product_dict[x].product_id.name for x in product_dict]}")
        for key  in invoice_lines:
            invoice_lines[key].write(  # we are writing in rma the invoice_line, invoice and state
                    {
                        "refund_line_id": key,
                        "refund_id": invoice.id,  # must be the original invoice
                        "state": "refunded",
                    }
                )
        invoice.ref=self.name
        invoice.action_post()
        return invoice

    def action_replace(self):
        """Invoked when 'Replace' button in rma form view is clicked."""
        self.ensure_one()
        stock_moves = []
        original_transfer_to_client = self.order_id.picking_ids.filtered(
            lambda r: r.picking_type_id.code == "outgoing"
        )[0]
        for rma in self.rma_ids:
            if rma.operation_id.name == "Replace" and rma.state not in [
                "draft",
                "cancelled",
                "replaced",
            ]:  #'refunded'
                if rma.product_uom_qty:
                    stock_moves.append(
                        (
                            0,
                            0,
                            {
                                "name": f"replace of {rma.product_id.name} in rma_group={self.name} rma={rma.name}",
                                "rma_id": rma.id,
                                "product_id": rma.product_id.id,
                                "product_uom_qty": rma.product_uom_qty,
                                "product_uom": rma.product_uom.id,
                                "warehouse_id": self.order_id.warehouse_id.id or False,
                                "partner_id": self.order_id.partner_shipping_id.id,
                                "company_id": self.order_id.company_id.id,
                                "sale_line_id": rma.move_id.sale_line_id.id,
                            },
                        )
                    )
                    rma.write({"state": "replaced"})
        print(f"stock_moves={stock_moves}")
        if stock_moves:
            replace_trans_to_client = self.env["stock.picking"].create(
                {
                    "partner_id": original_transfer_to_client.partner_id.id,
                    "picking_type_id": original_transfer_to_client.picking_type_id.id,
                    "location_id": original_transfer_to_client.location_id.id,
                    "location_dest_id": original_transfer_to_client.location_dest_id.id,
                    #                    'group_id':original_transfer_to_client.group_id.id, # with or without?
                    "sale_id": self.order_id.id,
                    "move_lines": stock_moves,
                    "origin": self.order_id.name,
                }
            )
            print(f"created replace_trans_to_client={replace_trans_to_client}")
            replace_trans_to_client.action_confirm()  # mark as to do, not draft order anymore
            replace_trans_to_client.action_assign() # to put also the quanitties

    def copy(self, default=None):
        raise ValidationError("It is not possibe to copy this object")

    def action_cancel(self):
        """Invoked when 'Cancel' button in rma form view is clicked."""
        for rma in self.rma_ids:
            rma.action_cancel()

    def action_draft(self):
        for rma in self.rma_ids:
            rma.action_draft()

    #    original_transfers = = fields.One2many('stock.picking',compute="_compute_group_state")
    invoices_ids = fields.One2many(
        "account.move", "rma_group_id", compute="_compute_group_state"
    )
    outgoing_transfers_ids = fields.One2many(
        "stock.picking", "rma_group_id", compute="_compute_group_state"
    )
    incomming_tranfers_ids = fields.One2many(
        "stock.picking", "rma_group_id", compute="_compute_group_state"
    )

    def action_view_incomming_transfers(self):
        self.ensure_one()
        action = (
            self.env.ref("stock.action_picking_tree_all")
            .with_context(active_id=self.id)
            .read()[0]
        )
        action.update(
            domain=[("id", "in", self.incomming_tranfers_ids.ids)],
            res_id=False,
            view_mode="tree,form",
            view_id=False,
            views=False,
        )
        return action

    def action_view_outgoing_transfers(self):
        """Invoked when 'Receipt' smart button in rma form view is clicked."""
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = (
            self.env.ref("stock.action_picking_tree_all")
            .with_context(active_id=self.id)
            .read()[0]
        )
        action.update(
            domain=[("id", "in", self.outgoing_transfers_ids.ids)],
            res_id=False,
            view_mode="tree,form",
            view_id=False,
            views=False,
        )
        return action

    def action_view_invoices(self):
        """Invoked when 'Refund' smart button in rma form view is clicked."""
        self.ensure_one()
        return {
            "name": _("Refund"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "views": False,  # [(self.env.ref("account.view_move_form").id, "form")],
            "res_id": False,
            "domain": [("id", "in", self.invoices_ids.ids)],
        }

    def action_preview(self):
        """Invoked when 'Preview' button in rma form view is clicked."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }
        
    def _get_report_base_filename(self):
        self.ensure_one()
        return f"{fields.datetime.now().strftime('%Y%m%d%H')} {self.name}" 
