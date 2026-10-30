import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_custom_fields():
	create_custom_fields({
		"Material Request": [{
			"fieldname": "custom_sales_order",
			"label": "Source Sales Order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
			"insert_after": "material_request_type",
		}],
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
	})
	# Remove the row-level cost field previously installed by this app.
	if frappe.db.exists("Custom Field", "Quotation Item-custom_cost"):
		frappe.delete_doc("Custom Field", "Quotation Item-custom_cost", ignore_permissions=True)
	for setter in frappe.get_all("Property Setter", filters={
		"doc_type": "Quotation Item", "property": "depends_on", "value": ["like", "%custom_cost%"],
	}, pluck="name"):
		frappe.delete_doc("Property Setter", setter, ignore_permissions=True)
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	meta = frappe.get_meta("Opportunity")
	options = (meta.get_field("status").options or "").splitlines()
	for status in ("Pending Cost", "Pending Pricing", "Pending Quotation"):
		if status not in options:
			options.append(status)
	make_property_setter("Opportunity", "status", "options", "\n".join(options), "Text")

	if not frappe.get_meta("Supplier").has_field("custom_supplier_item_group"):
		create_custom_fields({"Supplier": [{
			"fieldname": "custom_supplier_item_group",
			"label": "Item Groups",
			"fieldtype": "Table",
			"options": "Supplier Item Group",
		}]})
