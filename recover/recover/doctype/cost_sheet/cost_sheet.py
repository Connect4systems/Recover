# Copyright (c) 2025, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Costsheet(Document):
	pass


@frappe.whitelist()
def get_suppliers_for_item_group(doctype, txt, searchfield, start, page_len, filters=None):
	item_group = (filters or {}).get("item_group")
	if not item_group:
		return []

	suppliers = frappe.get_all(
		"Supplier Item Group",
		filters={
			"item_greoup": item_group,
			"parenttype": "Supplier",
			"parentfield": "custom_supplier_item_group",
		},
		pluck="parent",
	)
	if not suppliers:
		return []

	matches = frappe.get_list(
		"Supplier",
		filters={"name": ["in", suppliers], "disabled": 0},
		or_filters=[
			["Supplier", "name", "like", f"%{txt}%"],
			["Supplier", "supplier_name", "like", f"%{txt}%"],
		],
		fields=["name", "supplier_name"],
		start=start,
		page_length=page_len,
		order_by="name asc",
	)
	return [[supplier.name, supplier.supplier_name] for supplier in matches]
