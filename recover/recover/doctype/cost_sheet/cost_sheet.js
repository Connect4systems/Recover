// Copyright (c) 2025, Connect 4 Systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost sheet", {
	setup(frm) {
		frm.set_query("supplier", "items", function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				query: "recover.recover.doctype.cost_sheet.cost_sheet.get_suppliers_for_item_group",
				filters: { item_group: row.item_group },
			};
		});
	},
});

function update_cost_totals(frm, cdt, cdn) {
 const row = locals[cdt][cdn];
 frappe.model.set_value(cdt, cdn, "total_cost",
  flt(flt(row.price) + flt(row.other_cost), precision("total_cost", row)));
 update_sheet_total(frm);
}

function update_sheet_total(frm) {
 frm.set_value("total", (frm.doc.items || []).reduce(
  (total, row) => total + flt(row.total_cost) * flt(row.qty), 0));
}

frappe.ui.form.on("Cost Item", {
 price: update_cost_totals,
 other_cost: update_cost_totals,
 qty: update_sheet_total,
 items_remove: update_sheet_total,
});
