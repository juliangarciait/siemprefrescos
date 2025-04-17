{
    "name": "Credit Limit",
    "version": "1.0",
    "category": "Sales",
    "summary": "Manage customer credit limits and available credit.",
    "author": "Your Name",
    "depends": ["base", "sale"],
    "data": [
        "security/groups.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}