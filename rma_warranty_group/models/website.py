from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    rma_return_message = fields.Text(translate=True,default="For returning the products:\n-please put them into original package\n-On package write the address of our company")
