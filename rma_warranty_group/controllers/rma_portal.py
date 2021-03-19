from odoo.addons.rma.controllers.main import PortalRma
from odoo.http import request

class PortalRma(PortalRma):
    def _get_filter_domain(self, kw):
        res = super()._get_filter_domain(kw)
        if "sale_id" in kw:
            res.append(("order_id", "=", int(kw["sale_id"])))
#        res.append(("partner_id", "child_of", request.env.user.partner_id.id  ))      # i'll put it after the test and also in rma
        return res
