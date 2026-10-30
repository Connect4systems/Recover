"""Derive Opportunity progress from saved pricing and selling documents."""
import frappe


def sync_opportunity(doc, method=None):
    if doc.doctype == "Opportunity":
        name = doc.name
    else:
        name = doc.get("opportunity")
    if not name:
        return
    rows = frappe.db.sql(
        "select status from `tabOpportunity` where name=%s for update", (name,), as_dict=True,
    )
    if not rows or rows[0].status in ("Lost", "Closed"):
        return
    current = rows[0].status
    quotations = frappe.get_all("Quotation", filters={
        "opportunity": name, "docstatus": ["!=", 2],
    }, fields=["name", "docstatus", "custom_price_sheet"])
    cycle = frappe.db.exists("Price Request", {"opportunity": name, "docstatus": ["!=", 2]})
    cycle = cycle or any(q.custom_price_sheet for q in quotations)
    if not cycle:
        # Keep ordinary ERPNext opportunities on their standard status flow.
        if current not in ("Pending Cost", "Pending Pricing", "Pending Quotation"):
            return
        status = "Open"
    elif quotations and frappe.db.exists("Sales Order Item", {
        "prevdoc_docname": ["in", [q.name for q in quotations]],
        "parenttype": "Sales Order", "docstatus": 1,
    }):
        status = "Converted"
    elif any(q.docstatus == 1 for q in quotations):
        status = "Quotation"
    elif quotations:
        status = "Pending Quotation"
    elif frappe.db.exists("Price Sheet", {"opportunity": name, "docstatus": 1}):
        status = "Pending Quotation"
    elif frappe.db.exists("Cost sheet", {"opportunity": name, "docstatus": 1}):
        status = "Pending Pricing"
    elif frappe.db.exists("Price Request", {
        "opportunity": name, "docstatus": ["!=", 2], "workflow_state": "Pending Pricing",
    }):
        status = "Pending Cost"
    else:
        status = "Open"
    if current != status:
        frappe.db.set_value("Opportunity", name, "status", status)
    if doc.doctype == "Opportunity":
        doc.status = status


def sync_sales_order_opportunities(doc, method=None):
    for quotation in {row.get("prevdoc_docname") for row in doc.items if row.get("prevdoc_docname")}:
        sync_opportunity(frappe.get_doc("Quotation", quotation))
