from odoo import _, fields, models


class SaleOrderRmaWizard(models.TransientModel):
    _inherit = "sale.order.rma.wizard"

    description = fields.Text(
        help="A field to tell when was over the warranty for the products", readonly=1
    )

        #
    def create_and_open_rma_group(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda r: (r.quantity > 0.0) and r.operation_id )
        val_list = [(0,0,line._prepare_rma_values()) for line in lines]
        rma = self.env["rma.group"].create({ 'rma_ids':val_list, 'order_id':self.order_id.id})
        # post messages
        msg_list = [
            '<a href="#" data-oe-model="rma.group" data-oe-id="%d">%s</a>' % (r.id, r.name)
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
        action = self.env.ref("rma_warranty_group.rmagroup_action").read()[0]
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
        res['rma_reason_id'] = self.rma_reason_id.id
        return res

#
#     @api.depends("picking_id")
#     def _compute_move_id(self):
#         for record in self:
#             move_id = False
#             if record.picking_id:
#                 move_id = record.picking_id.move_lines.filtered(
#                     lambda r: (
#                         r.sale_line_id.product_id == record.product_id
#                         and r.sale_line_id.order_id == record.order_id
#                     )
#                 )
#             record.write(
#                 {
#                     "move_id": move_id.id if move_id else False,
#                     "uom_id": move_id.product_uom.id if move_id else False,
#                 }
#             )
#
#     @api.depends("order_id")
#     def _compute_allowed_product_ids(self):
#         for record in self:
#             product_ids = record.order_id.order_line.mapped("product_id.id")
#             record.allowed_product_ids = product_ids
#
#     @api.depends("product_id")
#     def _compute_allowed_picking_ids(self):
#         for record in self:
#             line = record.order_id.order_line.filtered(
#                 lambda r: r.product_id == record.product_id
#             )
#             record.allowed_picking_ids = line.mapped("move_ids.picking_id")
#
#     def _prepare_rma_values(self):
#         self.ensure_one()
#         return {
#             "partner_id": self.order_id.partner_id.id,
#             "partner_invoice_id": self.order_id.partner_invoice_id.id,
#             "origin": self.order_id.name,
#             "company_id": self.order_id.company_id.id,
#             "location_id": self.wizard_id.location_id.id,
#             "order_id": self.order_id.id,
#             "picking_id": self.picking_id.id,
#             "move_id": self.move_id.id,
#             "product_id": self.product_id.id,
#             "product_uom_qty": self.quantity,
#             "product_uom": self.uom_id.id,
#             "operation_id": self.operation_id.id,
#             "description": self.description,
#         }
