from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    rma_group_id = fields.Many2one(
        "rma.group", help="used just to compute the invoices per rma_group. "
    )
