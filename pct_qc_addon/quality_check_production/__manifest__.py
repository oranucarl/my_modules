{
    "name": "Quality Check Production Field",
    "version": "19.0.1.0.0",
    "category": "Manufacturing/Quality",
    "summary": "Add production order field to quality check list view",
    "description": """
        This module adds the production_id field to the quality.check
        list view, positioned after the operation_id field.
    """,
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "quality_control",
        "quality_mrp_workorder",
    ],
    "data": [
        "views/quality_check_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
