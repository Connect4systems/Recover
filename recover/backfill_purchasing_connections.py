"""Populate dashboard links without creating purchasing documents."""


def execute():
    import frappe
    from recover.cost_workflow import sync_material_request_connections, sync_purchase_order

    for name in frappe.get_all("Material Request", pluck="name"):
        sync_material_request_connections(frappe.get_doc("Material Request", name))
    for name in frappe.get_all("Purchase Order", pluck="name"):
        sync_purchase_order(frappe.get_doc("Purchase Order", name), update_status=False)
