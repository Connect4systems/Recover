import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_custom_fields():
	create_custom_fields({
		"Quotation": [{
			"fieldname": "custom_price_sheet",
			"label": "Price Sheet",
			"fieldtype": "Link",
			"options": "Price Sheet",
			"insert_after": "opportunity",
			"read_only": 1,
			"no_copy": 1,
		}, {
			"fieldname": "custom_cost_sheet",
			"label": "Cost Sheet",
			"fieldtype": "Link",
			"options": "Cost sheet",
			"insert_after": "opportunity",
			"read_only": 1,
			"no_copy": 1,
		}],
		"Quotation Item": [
			{
				"fieldname": "custom_cost",
				"label": "Cost",
				"fieldtype": "Currency",
				"options": "currency",
				"insert_after": "rate",
				"read_only": 1,
			},
		],
	})

	if not frappe.get_meta("Supplier").has_field("custom_item_group"):
		create_custom_fields({"Supplier": [{
			"fieldname": "custom_item_group",
			"label": "Item Groups",
			"fieldtype": "Table",
			"options": "Supplier Item Group",
		}]})
