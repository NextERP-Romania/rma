from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    def get_warranty_days(self,partner_id=False):
        "returns warranty days for products per client, or default 30"
        self.ensure_one()
        try:
            warranty = max(0, super().get_warranty_days(partner_id))
        except :
            warranty = 30
        return warranty
