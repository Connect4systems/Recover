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
		for row in self.items:
			row.item_group = frappe.get_cached_value("Item", row.item, "item_group")
			if row.supplier and (row.supplier not in get_item_group_suppliers(row.item_group) or frappe.db.get_value("Supplier", row.supplier, "disabled")):
				frappe.throw(frappe._("Supplier must be enabled and match the item group."))
			if flt(row.qty) <= 0:
				frappe.throw(frappe._("Item quantity must be greater than zero."))
			row.total_cost = flt(flt(row.price) + flt(row.other_cost), row.precision("total_cost"))
			self.total += row.total_cost * flt(row.qty)
		self.total = flt(self.total, self.precision("total"))

	def on_submit(self):
		if not self.opportunity or not self.items:
			frappe.throw(frappe._("An Opportunity and at least one item are required to submit a Cost Sheet."))
		if frappe.db.exists("Price Sheet", {"cost_sheet": self.name, "docstatus": ["!=", 2]}):
			return
		opportunity = frappe.get_doc("Opportunity", self.opportunity)
		price_sheet = frappe.new_doc("Price Sheet")
		price_sheet.update({
			"opportunity": self.opportunity,
			"cost_sheet": self.name,
			"party_type": opportunity.opportunity_from,
			"party": opportunity.party_name,
			"date": self.date,
		})
		for row in self.items:
			values = {field: row.get(field) for field in (
				"item", "item_name", "description", "uom", "qty", "price", "other_cost",
				"total_cost", "supplier",
			)}
			values.update(cost_sheet_item=row.name, profit=0, selling_price=row.total_cost)
			price_sheet.append("items", values)
		# Submitting purchase costs creates the sales team's draft pricing document.
		price_sheet.insert(ignore_permissions=True)


@frappe.whitelist()
def get_suppliers_for_item_group(doctype, txt, searchfield, start, page_len, filters=None):
	item_group = (filters or {}).get("item_group")
	if not item_group:
		return []

	suppliers = get_item_group_suppliers(item_group)
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


def get_item_group_suppliers(item_group):
	field = frappe.get_meta("Supplier").get_field("custom_supplier_item_group")
	if not field:
		frappe.throw(frappe._("Configure Supplier.custom_supplier_item_group before selecting suppliers."))
	if field.fieldtype == "Link" and field.options == "Item Group":
		return frappe.get_all("Supplier", filters={"custom_supplier_item_group": item_group}, pluck="name")
	if field.fieldtype in ("Table", "Table MultiSelect"):
		meta = frappe.get_meta(field.options)
		group_field = next((f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == "Item Group"), None)
		if group_field:
			return frappe.get_all(field.options, filters={
				group_field: item_group, "parenttype": "Supplier", "parentfield": "custom_supplier_item_group",
			}, pluck="parent")
	frappe.throw(frappe._("Supplier.custom_supplier_item_group must link to Item Group or contain an Item Group table."))
