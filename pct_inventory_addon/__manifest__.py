{
    "name": "PCT Inventory Addon",
    "version": "19.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Stock picking customizations with driver and truck info",
    "description": """
        Extends Stock Picking with:
        - Driver Name field
        - Truck Number field
        - Domain filter to exclude virtual locations
        - Show invoice/delivery status on SO list view
        - Show bill/receipt status on PO list view
    """,
    "author": "Carlson Oranu",
    "website": "https://www.packetclouds.com",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "sale_stock",
        "purchase_stock",
    ],
    "data": [
        "views/stock_picking_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
