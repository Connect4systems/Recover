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
			references = {row.name: row for row in opportunity.items}
			for row in self.items:
				if row.opportunity_item:
					source = references.get(row.opportunity_item)
					if not source or source.item_code != row.item:
						frappe.throw(frappe._("Item reference does not match the linked Opportunity."))


@frappe.whitelist()
def make_price_request(source_name, target_doc=None):
	return get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Price Request",
			"field_no_map": ["naming_series", "amended_from", "items"],
			"field_map": {"name": "opportunity", "opportunity_from": "party_type", "party_name": "party"},
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
			# Resolve legacy requests only when the item has one unambiguous source row.
			for row in target.items:
				if not row.opportunity_item:
					matches = [item for item in opportunity.items if item.item_code == row.item]
					if len(matches) == 1:
						row.opportunity_item = matches[0].name
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
