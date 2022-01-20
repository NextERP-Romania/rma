from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_group_id = fields.Many2one("rma.group", help="used just to compute the pickgins per rma_group ", readonly=1)
 
    # this is to function with some modules that are creating the invoices directely alter vlidation of transfer    
    def button_validate(self):
        if self.rma_group_id.id:
            self = self.with_context( skip_create_invoice_after_transfer=1)
        return  super(StockPicking,self).button_validate()