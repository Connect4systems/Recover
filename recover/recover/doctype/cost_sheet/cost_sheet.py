# Copyright (c) 2025, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Costsheet(Document):
	def on_submit(self):
		if not self.opportunity:
			return
		if not self.items:
			frappe.throw(frappe._("Add at least one item before submitting this Cost Sheet."))

		quotation_meta = frappe.get_meta("Quotation")
		quotation_filters = {}
		if quotation_meta.has_field("custom_cost_sheet"):
			quotation_filters["custom_cost_sheet"] = self.name
			if frappe.db.exists("Quotation", quotation_filters):
				return

		opportunity = frappe.get_doc("Opportunity", self.opportunity)
		if not opportunity.opportunity_from or not opportunity.party_name:
			frappe.throw(
				frappe._("Opportunity must have a party before a Quotation can be created.")
			)

		quotation = frappe.new_doc("Quotation")
		quotation.quotation_to = opportunity.opportunity_from
		quotation.party_name = opportunity.party_name
		quotation.opportunity = opportunity.name
		quotation.transaction_date = self.date
		if quotation_meta.has_field("custom_cost_sheet"):
			quotation.custom_cost_sheet = self.name

		for cost_item in self.items:
			quotation.append(
				"items",
				{
					"item_code": cost_item.item,
					"qty": cost_item.qty or 1,
					"rate": cost_item.total_cost or cost_item.price or 0,
				},
			)

		quotation.set_missing_values()
		quotation.insert(ignore_permissions=True)


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
