from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    rma_return_message = fields.Text(translate=True,default="For returning the products:\n-please put them into original package\n-On package write the address of our company")
