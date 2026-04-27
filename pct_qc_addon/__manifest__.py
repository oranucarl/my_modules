{
    "name": "PCT Quality Control Extensions",
    "version": "19.0.2.0.0",
    "category": "Manufacturing/Quality",
    "summary": "Add Sample Type, Samples, and production_id to Quality Control",
    "description": """
        Extends Quality Control module with:
        - Sample Type and Samples models
        - Sample Type and Samples fields on Control Points (quality.point)
        - Related Sample Type and Samples fields on Quality Checks (quality.check)
        - Production Order field on quality check list view
        - Configuration menus under Quality > Configuration
    """,
    "author": "Carlson Oranu",
    "website": "https://www.packetclouds.com",
    "license": "LGPL-3",
    "depends": [
        "mrp",
        "quality",
        "quality_control",
        "quality_mrp",
        "quality_mrp_workorder",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/quality_sample_type_views.xml",
        "views/quality_sample_views.xml",
        "views/quality_point_views.xml",
        "views/quality_check_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
