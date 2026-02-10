{
    "name": "Branch & Discount Based Pricelist",
    "summary": "Automatically select pricelist based on branch and customer discount",
    "version": "1.0.0",
    "category": "Sales",
    "author": "Packetclouds Technology Ltd",
    "website": "https://www.packetclouds.com",
    "license": "OPL-1",

    "depends": [
        "sale_management",
        "product",
        "pct_branches",
    ],

    "data": [
        "security/ir.model.access.csv",
        "data/sale_discount_data.xml",
        "views/sale_discount_views.xml",
        "views/res_partner_views.xml",
        "views/product_pricelist_views.xml",
    ],
    "post_init_hook": "set_default_partner_discount",
    "installable": True,
    "application": False,
}
