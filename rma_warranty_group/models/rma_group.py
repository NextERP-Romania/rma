from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaGroup(models.Model):
    _name = "rma.group"
    _description = "RMA Group"
    _order = "date desc"
    _inherit = ["mail.thread", "portal.mixin", "mail.activity.mixin"]

    @api.depends()
    def _compute_name(self):
        for rec in self:
            if rec.name:
                continue
            else:
                latest_rma = rec.search_read(
                    [("order_id", "=", rec.order_id.id)],
                    ["name"],
                    order="id desc",
                    limit=1,
                )
                if latest_rma:
                    orginal_name = latest_rma[1]
                    nr_position = orginal_name.rfind("#")
                    if nr_position:
                        name = orginal_name[:nr_position] + str(
                            int(orginal_name[nr_position:]) + 1
                        )
                    else:
                        name = orginal_name + "#1"
                else:
                    name = rec.sale_order.name
                rec.name = "RMAG/" + name

    order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order", readonly=1
    )

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/rmags/{}".format(record.id)

    def write(self, values):
        if "order_id" in values:
            raise ValidationError("You can not change a order_id of a rma_group")
        return super().write(values)

    sent = fields.Boolean()
    name = fields.Char(string="Name", index=True, computed="_compute_name", store=True)
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
            ("cancelled", "Canceled"),
        ],
        store="1",
        compute="_compute_group_state",
    )
    rma_ids = fields.One2many("rma", "rma_group_id")
    finised = fields.Boolean(
        help="if this is true, means that we do not need to do anything with this group"
    )

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
            elif all([x == "concelled" for x in states]):
                state = "cancelled"
            elif all([x in ["refunded", "returned", "replaced"] for x in states]):
                state = "resolved"
            else:
                state = "mixt"
            rec.state = state

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

    refund_ids = fields.Many2one(
        comodel_name="account.move",
        string="Refund",
        readonly=True,
        copy=False,
    )

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
        will call the _crate_reception_from_picking and _from_product  in rma
        """
        self.ensure_one()
        for rma in self.rma.ids:
            rma.action_confirm()

    def action_refund(self):
        """Invoked when 'Refund' button in rma form view is clicked
        and 'rma_refund_action_server' server action is run.
        """
        self.ensure_one()
        for rma in self.rma.ids:
            rma.action_refund()

    def action_replace(self):
        """Invoked when 'Replace' button in rma form view is clicked."""
        for rma in self.rma.ids:
            r = rma.action_replace()
        return r

    def copy(self, default=None):
        raise ValidationError("It is not possibe to copy this object")

    def action_cancel(self):
        """Invoked when 'Cancel' button in rma form view is clicked."""
        for rma in self.rma.ids:
            rma.action_cancel()

    def action_draft(self):
        for rma in self.rma.ids:
            rma.action_draft()

    def action_preview(self):
        """Invoked when 'Preview' button in rma form view is clicked."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }
