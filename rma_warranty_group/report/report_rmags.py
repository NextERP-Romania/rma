from odoo import api, models


class RerpotAlsoWithOtherValue(models.AbstractModel):
    _name="report.rma_warranty_group.report_rmag"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.sudo().env['rma.group'].browse(docids)
        rma_return_message = records[0].company_id.rma_return_message if records else ''
        docargs = {
            'doc_ids': docids,
            'rma_return_message':rma_return_message,
            'doc_model': 'rma.group',
            'docs': records,
        }
        return docargs
    
    