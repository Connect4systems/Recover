# Copyright (c) 2025, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PriceRequest(Document):
	pass


@frappe.whitelist()
def make_cost_sheet(source_name, target_doc=None):
	price_request = frappe.get_doc("Price Request", source_name)
	price_request.check_permission("read")

	cost_sheet = frappe.new_doc("Cost sheet")
	cost_sheet.price_request = price_request.name
	cost_sheet.opportunity = price_request.opportunity
	cost_sheet.date = price_request.date

	if price_request.opportunity:
		opportunity = frappe.get_doc("Opportunity", price_request.opportunity)
		cost_sheet.opportunity_from = opportunity.opportunity_from
		cost_sheet.party = opportunity.party_name

	for price_item in price_request.items:
		cost_item = cost_sheet.append(
			"items",
			{
				"item": price_item.item,
				"qty": price_item.qty,
			},
		)
		cost_item.item_name, cost_item.item_group = frappe.get_cached_value(
			"Item", price_item.item, ["item_name", "item_group"]
		)

		if price_request.opportunity:
			opportunity_items = frappe.get_all(
				"Opportunity Item",
				filters={
					"parent": price_request.opportunity,
					"parenttype": "Opportunity",
					"parentfield": "items",
					"item_code": price_item.item,
				},
				pluck="name",
			)
			if len(opportunity_items) == 1:
				cost_item.opportunity_item = opportunity_items[0]

	return cost_sheet
