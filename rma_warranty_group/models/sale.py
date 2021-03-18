from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # RMA_Groups that were created from a sale order
    rma_group_ids = fields.One2many(
        comodel_name="rma.group",
        inverse_name="order_id",
        string="RMA Groups",
        copy=False,
    )
    rma_group_count = fields.Integer(
        string="RMA Group count", compute="_compute_rma_group_count"
    )

    def _compute_rma_group_count(self):
        rma_group_data = self.env["rma.group"].read_group(
            [("order_id", "in", self.ids)], ["order_id"], ["order_id"]
        )
        mapped_data = {r["order_id"][0]: r["order_id_count"] for r in rma_group_data}
        for record in self:
            record.rma_group_count = mapped_data.get(record.id, 0)

    def action_create_rma_group(self):
        self.ensure_one()
        if self.state not in ["sale", "done"]:
            raise ValidationError(
                _("You may only create RMAs from a " "confirmed or done sale order.")
            )
        wizard_obj = self.env["sale.order.rma.wizard"]
        get_delivery_rma_group_data = self.get_delivery_rma_group_data()
        line_vals = [
            (
                0,
                0,
                {
                    "product_id": data["product"].id,
                    "quantity": data["quantity"],
                    "move_id": data["move_id"] and data["move_id"].id,
                    "uom_id": data["uom"].id,
                    "picking_id": data["picking"] and data["picking"].id,
                    "operation_id": self.env["rma.operation"]
                    .search([("id", ">", -1)], order="id", limit=1)
                    .id,
                },
            )
            for data in get_delivery_rma_group_data[0]
        ]
        wizard = wizard_obj.with_context(active_id=self.id).create(
            {
                "line_ids": line_vals,
                "description": get_delivery_rma_group_data[1],
                "location_id": self.warehouse_id.rma_loc_id.id,
            }
        )

        return {
            "name": _("Create Group RMA"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.order.rma.wizard",
            "res_id": wizard.id,
            "views":[(self.env.ref("rma_warranty_group.sale_order_rma_reson_wizard_form_view").id,'form')],
            "target": "new",
        }

    def action_view_rma_group(self):
        self.ensure_one()
        action = self.env.ref("rma_warranty_group.rma_groupaction").read()[0]
        rma = self.rma_group_ids
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
                views=[],
            )
        else:
            action["domain"] = [("id", "in", rma.ids)]
        # reset context to show all related rma without default filters
        action["context"] = {}
        return action

    def get_delivery_rma_group_data(self):
        """in this function we are going to give only the lines that have moves on them
        and also are in warranty"""
        self.ensure_one()
        data = []
        description = ""
        for line in self.order_line:
            #            data += line.prepare_sale_rma_data()
            product = line.product_id
            if product.type != "product":
                description += (
                    f"- product {product.name} not stockable is type {product.type}\n"
                )
                continue
            moves = line.move_ids.filtered(
                lambda r: (
                    product == r.product_id
                    and r.state == "done"
                    and not r.scrapped
                    and r.location_dest_id.usage == "customer"
                    and (
                        not r.origin_returned_move_id
                        or (r.origin_returned_move_id and r.to_refund)
                    )
                )
            )
            if not moves:
                description += f"- product {product.name} not does not have done moves to customer, or is a returned/to_refund move\n"
            else:
                for move in moves:
                    warranty_till = move.date + timedelta(
                        days=product.product_tmpl_id.get_warranty_days(move.partner_id)
                    )
                    if fields.datetime.today() > warranty_till:
                        description += f"- product {product.name} is not anymore in warranty, warranty ended {warranty_till}"
                        continue
                    qty = move.product_uom_qty
                    move_dest = move.move_dest_ids.filtered(
                        lambda r: r.state in ["partially_available", "assigned", "done"]
                    )
                    qty -= sum(move_dest.mapped("product_uom_qty"))
                    data.append(
                        {
                            "product": product,
                            "quantity": qty,
                            "move_id": move,
                            "uom": move.product_uom,
                            "picking": move.picking_id,
                        }
                    )

        return data, description
