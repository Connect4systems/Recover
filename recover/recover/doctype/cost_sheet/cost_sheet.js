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
		frm.set_query("opportunity_item", "items", function () {
			return {
				filters: {
					parent: frm.doc.opportunity,
					parenttype: "Opportunity",
					parentfield: "items",
				},
			};
		});
	},
});
