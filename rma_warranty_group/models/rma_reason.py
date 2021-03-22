from odoo import fields, models


class RmaReason(models.Model):
    _name = "rma.reason"
    _inherit = "mail.thread"
    _description = "reasons for a RMA"
    _order = "name"

    name = fields.Char(tracking=1)
