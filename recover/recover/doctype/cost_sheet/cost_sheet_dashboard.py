from frappe import _


def get_data():
    return {
        "fieldname": "cost_sheet",
        "internal_links": {
            "Material Request": ["purchasing_connections", "material_request"],
            "Purchase Order": ["purchasing_connections", "purchase_order"],
        },
        "transactions": [
            {"label": _("Pricing"), "items": ["Price Sheet"]},
            {"label": _("Purchasing"), "items": ["Material Request", "Purchase Order"]},
        ],
    }
