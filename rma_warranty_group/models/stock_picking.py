from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_group_id = fields.Many2one(
        "rma.group", help="used just to compute the pickgins per rma_group. "
    )
