# Copyright 2021 Next-ERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management Grouping and Warranty",
    "summary": "Return Merchandise Authorization (RMA)  Grouping and Warranty",
    "description": """ now the RMA's have groups
    like in wizard and you are able to process more RMA at once
    in wizard you are going to have only products that are in warranty period
    """,
    "version": "14.0.0.1.0",
    "development_status": "Development",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "NextERP Romaina",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
    "depends": ["rma_sale", "stock"],
    "data": [
        "security/rma_group_security.xml",
        "security/ir.model.access.csv",
        "report/report.xml",
        "data/mail_data.xml",
        "views/rma_operation.xml",
        "views/res_partner_views.xml",
        "views/rma_group_views.xml",
        "views/rma_views.xml",
        "views/rma_reason.xml",
        "views/sale_views.xml",
        "wizard/sale_order_rma_wizard_views.xml",
        "views/rma_portal_templates.xml",
        "views/sale_portal_template.xml",
        "views/website_views.xml",
        
        "views/report_rmag.xml",
    ],
    "application": False,
}
