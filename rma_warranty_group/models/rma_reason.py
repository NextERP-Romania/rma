from odoo import models,fields

class RmaReason(models.Model):
    _name="rma.reason"
    _inherit = "mail.thread"
    _description ="reasons for a RMA"
    _order = "name"
    
    name = fields.Char(traking=1) 