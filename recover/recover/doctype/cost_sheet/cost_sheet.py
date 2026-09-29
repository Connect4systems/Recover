# Copyright (c) 2025, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Costsheet(Document):
	def validate(self):
		from frappe.utils import flt

		self.total = 0
		if self.price_request:
			request = frappe.get_doc("Price Request", self.price_request)
			request.check_permission("read")
			if request.docstatus == 2 or request.opportunity != self.opportunity:
				frappe.throw(frappe._("Cost Sheet must match an active Price Request and its Opportunity."))
		opportunity = frappe.get_doc("Opportunity", self.opportunity) if self.opportunity else None
		references = {row.name: row for row in opportunity.items} if opportunity else {}
		for row in self.items:
			if flt(row.qty) <= 0:
				frappe.throw(frappe._("Item quantity must be greater than zero."))
			if row.opportunity_item:
				source = references.get(row.opportunity_item)
				if not source or source.item_code != row.item:
					frappe.throw(frappe._("Item reference does not match the linked Opportunity."))
			row.total_cost = flt(flt(row.price) + flt(row.other_cost), row.precision("total_cost"))
			self.total += row.total_cost * flt(row.qty)
		self.total = flt(self.total, self.precision("total"))

	def on_submit(self):
		if not self.opportunity:
			return
		if not self.items:
			frappe.throw(frappe._("Add at least one item before submitting this Cost Sheet."))
		if frappe.db.exists("Quotation", {"custom_cost_sheet": self.name, "docstatus": ["!=", 2]}):
			return

		opportunity = frappe.get_doc("Opportunity", self.opportunity)
		quotation = frappe.new_doc("Quotation")
		quotation.update({
			"quotation_to": opportunity.opportunity_from,
			"party_name": opportunity.party_name,
			"company": opportunity.company,
			"currency": opportunity.currency,
			"opportunity": opportunity.name,
			"custom_cost_sheet": self.name,
			"transaction_date": self.date,
		})
		for field in ("customer_address", "contact_person", "campaign", "source"):
			if opportunity.get(field):
				quotation.set(field, opportunity.get(field))
		source_items = {row.name: row for row in opportunity.items}
		for cost_item in self.items:
			source = source_items.get(cost_item.opportunity_item)
			values = {
				"item_code": cost_item.item,
				"item_name": cost_item.item_name,
				"description": cost_item.description or (source.description if source else None),
				"uom": cost_item.uom or (source.uom if source else None),
				"qty": cost_item.qty,
				"prevdoc_docname": opportunity.name,
				"prevdoc_doctype": "Opportunity",
				"custom_opportunity_item": cost_item.opportunity_item,
				"custom_cost": cost_item.total_cost,
			}
			if source:
				values["rate"] = source.rate
			quotation.append("items", values)
		quotation.set_missing_values()
		quotation.calculate_taxes_and_totals()
		# Submission is the purchase user's authorized action that creates a sales draft.
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
