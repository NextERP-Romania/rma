from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    rma_group_ids = fields.One2many(
        comodel_name="rma.group",
        inverse_name="partner_id",
        string="RMAs",
    )
    rma_group_count = fields.Integer(
        string="RMA count",
        compute="_compute_rmag_count",
    )



    def _compute_rmag_count(self):
        rma_data = self.env["rma.group"].read_group(
            [("partner_id", "in", self.ids)], ["partner_id"], ["partner_id"]
        )
        mapped_data = {r["partner_id"][0]: r["partner_id_count"] for r in rma_data}
        for record in self:
            record.rma_count = mapped_data.get(record.id, 0)

    def action_view_rmag(self):
        self.ensure_one()
        action = self.env.ref("rma_warranty_group.rma_groupaction").read()[0]
        rmag = self.rmag_ids
        if len(rmag) == 1:
            action.update(
                res_id=rmag.id,
                view_mode="form",
                view_id=False,
                views=False,
            )
        else:
            action["domain"] = [("partner_id", "in", self.ids)]
        return action
