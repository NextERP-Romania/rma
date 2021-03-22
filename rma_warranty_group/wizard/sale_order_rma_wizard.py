from odoo import _, fields, models


class SaleOrderRmaWizard(models.TransientModel):
    _inherit = "sale.order.rma.wizard"

    description = fields.Text(
        help="A field to tell when was over the warranty for the products", readonly=1
    )

    def create_and_open_rma_group(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda r: (r.quantity > 0.0) and r.operation_id)
        val_list = [(0, 0, line._prepare_rma_values()) for line in lines]
        rma = self.env["rma.group"].create(
            {"rma_ids": val_list, "order_id": self.order_id.id}
        )
        # post messages
        msg_list = [
            '<a href="#" data-oe-model="rma.group" data-oe-id="%d">%s</a>'
            % (r.id, r.name)
            for r in rma
        ]
        msg = ", ".join(msg_list)
        if len(msg_list) == 1:
            self.order_id.message_post(body=_(msg + " has been created."))
        elif len(msg_list) > 1:
            self.order_id.message_post(body=_(msg + " have been created."))
        rma.message_post_with_view(
            "mail.message_origin_link",
            values={"self": rma, "origin": self.order_id},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        action = self.env.ref("rma_warranty_group.rma_groupaction").read()[0]
        action.update(
            res_id=rma.id,
            view_mode="form",
            view_id=False,
            views=False,
        )
        return action


class SaleOrderLineRmaWizard(models.TransientModel):
    _inherit = "sale.order.line.rma.wizard"

    rma_reason_id = fields.Many2one(comodel_name="rma.reason")

    def _prepare_rma_values(self):
        res = super()._prepare_rma_values()
        res["rma_reason_id"] = self.rma_reason_id.id
        return res


#
