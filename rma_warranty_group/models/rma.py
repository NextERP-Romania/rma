from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

 
class Rma(models.Model):
    _inherit = "rma"

    rma_group_id = fields.Many2one(
        'rma.group', 'RMA Group',
         index=True, ondelete="cascade")
    rma_reason_id = fields.Many2one("rma.reason")






