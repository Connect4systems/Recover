# Copyright (c) 2025, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class PriceRequest(Document):
	def validate(self):
		if self.opportunity:
			opportunity = frappe.get_doc("Opportunity", self.opportunity)
			self.party_type = opportunity.opportunity_from
			self.party = opportunity.party_name


def complete_price_request(name):
	"""Complete purchasing through the configured workflow in the caller's transaction."""
	from frappe.model.workflow import apply_workflow

	request = frappe.get_doc("Price Request", name)
	request.check_permission("read")
	if request.docstatus == 1 and request.get("workflow_state") == "Pricing Complete":
		return
	if request.docstatus != 0 or request.get("workflow_state") != "Pending Pricing":
		frappe.throw(frappe._("Price Request must be Pending Pricing before submitting its Cost Sheet."))
	# Keep workflow roles, conditions, submission hooks, and audit history intact.
	completed = apply_workflow(request, "Done")
	if completed.docstatus != 1 or completed.get("workflow_state") != "Pricing Complete":
		frappe.throw(frappe._("The Price Request Done action must submit it as Pricing Complete."))


@frappe.whitelist()
def make_price_request(source_name, target_doc=None):
	return get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Price Request",
			"field_no_map": ["naming_series", "amended_from", "items"],
			"field_map": {"name": "opportunity", "opportunity_from": "party_type", "party_name": "party"},
		},
		"Opportunity Item": {
			"doctype": "Pricing Items",
			"field_map": {
				"item_code": "item",
				"item_name": "item_name",
				"description": "description",
				"uom": "uom",
				"qty": "qty",
			},
		},
	}, target_doc)


@frappe.whitelist()
def make_cost_sheet(source_name, target_doc=None):
	def populate(source, target):
		if source.docstatus == 2:
			frappe.throw(frappe._("Cannot create a Cost Sheet from a cancelled Price Request."))
		if source.opportunity:
			opportunity = frappe.get_doc("Opportunity", source.opportunity)
			target.opportunity_from = opportunity.opportunity_from
			target.party = opportunity.party_name
		for row in target.items:
			row.item_group = frappe.get_cached_value("Item", row.item, "item_group")

	return get_mapped_doc("Price Request", source_name, {
		"Price Request": {
			"doctype": "Cost sheet",
			"field_no_map": ["naming_series", "amended_from"],
			"field_map": {"name": "price_request"},
		},
		"Pricing Items": {"doctype": "Cost Item", "field_map": {"name": "price_request_item", "item": "item", "item_name": "item_name", "description": "description", "uom": "uom", "qty": "qty"}},
	}, target_doc, populate)
