from odoo import _, exceptions, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import consteq

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalRmaGroup(CustomerPortal):
    def _prepare_portal_layout_rma_group_values(self):
        values = super()._prepare_portal_layout_values()
        if request.env["rma.group"].check_access_rights("read", raise_exception=False):
            values["rma_group_count"] = request.env["rma.group"].search_count([])
        else:
            values["rma_group_count"] = 0
        return values

    def _rmag_get_page_view_values(self, rma_group, access_token, **kwargs):
        values = {
            "page_name": "RMA GROUPS",
            "rma_group": rma_group,
        }
        return self._get_page_view_values(
            rma_group, access_token, values, "my_rmags_history", False, **kwargs
        )

    @http.route(
        ["/my/rmags", "/my/rmags/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_rmags(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_rma_group_values()
        rma_group_obj = request.env["rma.group"]
        domain = self._get_filter_domain(kw)
        searchbar_sortings = {
            "date": {"label": _("Date"), "order": "date desc"},
            "name": {"label": _("Name"), "order": "name desc"},
            "state": {"label": _("Status"), "order": "state"},
        }
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]
        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]
        # count for pager
        rma_group_count = rma_group_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/rmags",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
            },
            total=rma_group_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        rmags = rma_group_obj.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_rmags_history"] = rmags.ids[:100]
        values.update(
            {
                "date": date_begin,
                "rmags": rmags,
                "page_name": "RMA Groups",
                "pager": pager,
                "some_value":'value 44',
                #                "archive_groups": archive_groups,
                "default_url": "/my/rmags",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        print(values)
        return request.render("rma_warranty_group.portal_my_rmags", values)

    @http.route(
        ["/my/rmags/<int:rma_group_id>"], type="http", auth="public", website=True
    )
    def portal_my_rmag_detail(
        self, rma_group_id, access_token=None, report_type=None, download=False, **kw
    ):
        try:
            rma_sudo = self._document_check_access(
                "rma.group", rma_group_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=rma_sudo,
                report_type=report_type,
                report_ref="rma_group.report_rma_group_action",
                download=download,
            )

        values = self._rmag_get_page_view_values(rma_sudo, access_token, **kw)
        return request.render("rma_warranty_group.portal_rmag_page", values)

    @http.route(
        ["/my/rmag/picking/pdf/<int:rma_group_id>/<int:picking_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_rmag_picking_report(
        self, rma_group_id, picking_id, access_token=None, **kw
    ):
        try:
            picking_sudo = self._picking_check_access(
                rma_group_id, picking_id, access_token=access_token
            )
        except exceptions.AccessError:
            return request.redirect("/my")
        report_sudo = request.env.ref("stock.action_report_delivery").sudo()
        pdf = report_sudo.render_qweb_pdf([picking_sudo.id])[0]
        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    def _picking_check_access(self, rma_group_id, picking_id, access_token=None):
        rma = request.env["rma.group"].browse([rma_group_id])
        picking = request.env["stock.picking"].browse([picking_id])
        picking_sudo = picking.sudo()
        try:
            picking.check_access_rights("read")
            picking.check_access_rule("read")
        except exceptions.AccessError:
            if not access_token or not consteq(rma.access_token, access_token):
                raise
        return picking_sudo
