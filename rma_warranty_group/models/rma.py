from odoo import fields, models


class Rma(models.Model):
    _inherit = "rma"

    rma_group_id = fields.Many2one(
        "rma.group", "RMA Group", index=True, ondelete="cascade"
    )
    rma_reason_id = fields.Many2one("rma.reason",required=1,default=lambda r: r.env.ref('rma_warranty_group.before_rma_reason_required').id)
