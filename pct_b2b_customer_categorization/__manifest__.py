# -*- coding: utf-8 -*-
{
    "name": "B2B Customer Categorization",
    "version": "18.0.1.0.0",
    "summary": "Tier customers by monthly/period spend with alerts and tags",
    "category": "Sales/CRM",
    "author": "Carlson Oranu",
    "license": "LGPL-3",
    "depends": ["base", "mail", "contacts", "sale", "account", "crm", "sale_management", "sales_team"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "data/cron.xml",
        "data/seed.xml",
        "views/b2b_category_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "application": False,
    "installable": True,
}
