import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PriceSheet(Document):
	def on_submit(self):
		from recover.cost_workflow import update_cost_status

		update_cost_status(self.cost_sheet, "Price Complete")
		quotation = make_quotation(self.name)
		self.quotation = quotation.name
		frappe.db.set_value("Price Sheet", self.name, "quotation", quotation.name)

	def validate(self):
		cost_sheet = frappe.get_doc("Cost sheet", self.cost_sheet)
		if cost_sheet.docstatus != 1:
			frappe.throw(frappe._("Price Sheet requires a submitted Cost Sheet."))
		if self.opportunity != cost_sheet.opportunity:
			frappe.throw(frappe._("Opportunity must match the Cost Sheet."))
		opportunity = frappe.get_doc("Opportunity", self.opportunity)
		self.party_type = opportunity.opportunity_from
		self.party = opportunity.party_name
		source_rows = {row.name: row for row in cost_sheet.items}
		seen = set()
		self.total = 0
		for row in self.items:
			source = source_rows.get(row.cost_sheet_item)
			if not source or row.cost_sheet_item in seen:
				frappe.throw(frappe._("Each Price Sheet item must reference a unique Cost Sheet row."))
			seen.add(row.cost_sheet_item)
			for field in ("item", "item_name", "description", "uom", "qty", "price", "supplier"):
				row.set(field, source.get(field))
			row.other_cost = flt(row.get("other_cost"))
			row.total_cost = flt(flt(row.price) + row.other_cost, row.precision("total_cost"))
			row.selling_price = flt(flt(row.total_cost) + flt(row.profit), row.precision("selling_price"))
			self.total += flt(row.qty) * row.selling_price
		if not source_rows or seen != set(source_rows):
			frappe.throw(frappe._("Price Sheet must contain all Cost Sheet items."))
		self.total = flt(self.total, self.precision("total"))


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	price_sheet = frappe.get_doc("Price Sheet", source_name)
	price_sheet.check_permission("read")
	frappe.has_permission("Quotation", "create", throw=True)
	if price_sheet.docstatus != 1:
		frappe.throw(frappe._("Submit the Price Sheet before creating a Quotation."))
	if frappe.db.get_value("Cost sheet", price_sheet.cost_sheet, "docstatus") != 1:
		frappe.throw(frappe._("The linked Cost Sheet must remain submitted."))
	# Serialize retries so a Price Sheet has only one active quotation.
	frappe.db.sql("select name from `tabPrice Sheet` where name=%s for update", (source_name,))
	existing = frappe.db.get_value("Quotation", {
		"custom_price_sheet": source_name, "docstatus": ["!=", 2],
	}, "name")
	if existing:
		quotation = frappe.get_doc("Quotation", existing)
		quotation.check_permission("read")
		return quotation
	opportunity = frappe.get_doc("Opportunity", price_sheet.opportunity)
	quotation = frappe.new_doc("Quotation")
	quotation.update({
		"quotation_to": price_sheet.party_type,
		"party_name": price_sheet.party,
		"company": opportunity.company,
		"currency": opportunity.currency,
		"opportunity": opportunity.name,
		"custom_cost_sheet": price_sheet.cost_sheet,
		"custom_price_sheet": price_sheet.name,
		"ignore_pricing_rule": 1,
	})
	for field in ("customer_address", "contact_person", "campaign", "source"):
		if opportunity.get(field):
			quotation.set(field, opportunity.get(field))
	for row in price_sheet.items:
		quotation.append("items", {
			"item_code": row.item,
			"item_name": row.item_name,
			"description": row.description,
			"uom": row.uom,
			"qty": row.qty,
			"rate": row.selling_price,
		})
	quotation.set_missing_values()
	for item, source in zip(quotation.items, price_sheet.items):
		item.rate = source.selling_price
	quotation.calculate_taxes_and_totals()
	quotation.insert()
	return quotation
