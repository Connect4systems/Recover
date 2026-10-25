"""Propagate purchasing and selling progress to the originating Cost Sheet."""
import frappe


STAGES = {"Draft": 0, "Pending Price": 1, "Price Complete": 2,
          "Quotation": 3, "Sales Order": 4, "PO": 5}


def update_cost_status(name, stage, status=None):
    if not name:
        return
    # Lock the source so simultaneous document events cannot regress its stage.
    rows = frappe.db.sql(
        "select status, docstatus from `tabCost sheet` where name=%s for update", (name,),
        as_dict=True,
    )
    if not rows or rows[0].docstatus != 1:
        return
    current = (rows[0].status or "Draft").split(" - ", 1)[0]
    if STAGES.get(current, 0) > STAGES[stage]:
        return
    value = f"{stage} - {status}" if status else stage
    if rows[0].status != value:
        frappe.db.set_value("Cost sheet", name, "status", value)


def quotation_cost_sheets(doc):
    sheets = set()
    if doc.get("custom_cost_sheet"):
        sheets.add(doc.custom_cost_sheet)
    elif doc.get("custom_price_sheet"):
        name = frappe.db.get_value("Price Sheet", doc.custom_price_sheet, "cost_sheet")
        if name:
            sheets.add(name)
    return sheets


def sales_order_cost_sheets(doc):
    sheets = set()
    for name in {row.get("prevdoc_docname") for row in doc.items if row.get("prevdoc_docname")}:
        sheets.update(quotation_cost_sheets(frappe.get_doc("Quotation", name)))
    return sheets


def sync_quotation(doc, method=None):
    for name in quotation_cost_sheets(doc):
        update_cost_status(name, "Quotation", doc.status)


def sync_sales_order(doc, method=None):
    for name in sales_order_cost_sheets(doc):
        update_cost_status(name, "Sales Order", doc.status)


def create_material_request(doc, method=None):
    sheets = sales_order_cost_sheets(doc)
    if not sheets:
        return
    # A stable Sales Order reference also prevents duplicate drafts on retries.
    existing = frappe.db.get_value("Material Request", {
        "custom_sales_order": doc.name, "docstatus": ["!=", 2],
    }, "name")
    if not existing:
        from erpnext.selling.doctype.sales_order.sales_order import make_material_request

        request = make_material_request(doc.name)
        if not request.items:
            return
        request.material_request_type = "Purchase"
        request.custom_sales_order = doc.name
        request.insert(ignore_permissions=True)
        existing = request.name
    for name in sheets:
        frappe.db.set_value("Cost sheet", name, "material_request", existing)
    sync_sales_order(doc)


def sync_purchase_order(doc, method=None):
    # A draft PO has not yet been issued.
    if doc.docstatus == 0:
        return
    sheets = set()
    for name in {row.get("material_request") for row in doc.items if row.get("material_request")}:
        request = frappe.get_doc("Material Request", name)
        sheets.update(frappe.get_all("Cost sheet", filters={"material_request": name}, pluck="name"))
        orders = {row.get("sales_order") for row in request.items if row.get("sales_order")}
        if request.get("custom_sales_order"):
            orders.add(request.custom_sales_order)
        for order in orders:
            sheets.update(sales_order_cost_sheets(frappe.get_doc("Sales Order", order)))
    for name in sheets:
        update_cost_status(name, "PO", doc.status)


def sync_fulfilment(doc, method=None):
    """ERPNext updates order statuses directly when receipts/invoices are posted."""
    sales_orders = set()
    purchase_orders = set()
    for row in doc.items:
        if row.get("sales_order"):
            sales_orders.add(row.sales_order)
        if row.get("against_sales_order"):
            sales_orders.add(row.against_sales_order)
        if row.get("purchase_order"):
            purchase_orders.add(row.purchase_order)
    for name in sales_orders:
        sync_sales_order(frappe.get_doc("Sales Order", name))
    for name in purchase_orders:
        sync_purchase_order(frappe.get_doc("Purchase Order", name))


def backfill_cost_sheet_statuses():
    """Rebuild existing progress from explicit links without creating documents."""
    sheets = frappe.get_all("Cost sheet", filters={"docstatus": 1}, pluck="name")
    if not sheets:
        return 0
    prices = frappe.get_all("Price Sheet", filters={
        "cost_sheet": ["in", sheets], "docstatus": ["!=", 2],
    }, fields=["name", "cost_sheet", "docstatus"], order_by="modified asc, name asc")
    for price in prices:
        update_cost_status(price.cost_sheet, "Price Complete" if price.docstatus == 1 else "Pending Price")

    links = [["custom_cost_sheet", "in", sheets]]
    if prices:
        links.append(["custom_price_sheet", "in", [price.name for price in prices]])
    quotations = frappe.get_all("Quotation", or_filters=links,
                                pluck="name", order_by="modified asc, name asc")
    for name in quotations:
        sync_quotation(frappe.get_doc("Quotation", name))

    orders = set()
    if quotations:
        orders.update(frappe.get_all("Sales Order Item", filters={
            "prevdoc_docname": ["in", quotations], "parenttype": "Sales Order",
        }, pluck="parent"))
    if orders:
        for name in frappe.get_all("Sales Order", filters={"name": ["in", sorted(orders)]},
                                   pluck="name", order_by="modified asc, name asc"):
            sync_sales_order(frappe.get_doc("Sales Order", name))

    requests = set(frappe.get_all("Cost sheet", filters={"name": ["in", sheets],
        "material_request": ["is", "set"]}, pluck="material_request"))
    if orders:
        requests.update(frappe.get_all("Material Request Item", filters={
            "sales_order": ["in", sorted(orders)], "parenttype": "Material Request",
        }, pluck="parent"))
        requests.update(frappe.get_all("Material Request", filters={
            "custom_sales_order": ["in", sorted(orders)],
        }, pluck="name"))
    if requests:
        purchases = set(frappe.get_all("Purchase Order Item", filters={
            "material_request": ["in", sorted(requests)], "parenttype": "Purchase Order",
        }, pluck="parent"))
        if purchases:
            for name in frappe.get_all("Purchase Order", filters={
                "name": ["in", sorted(purchases)], "docstatus": ["!=", 0],
            }, pluck="name", order_by="modified asc, name asc"):
                sync_purchase_order(frappe.get_doc("Purchase Order", name))
    return len(sheets)
