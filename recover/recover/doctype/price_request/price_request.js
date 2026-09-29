// Copyright (c) 2025, Connect 4 Systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Price Request", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus === 2) {
			return;
		}

		frm.add_custom_button(__("Cost Sheet"), function () {
			frappe.model.open_mapped_doc({
				method: "recover.recover.doctype.price_request.price_request.make_cost_sheet",
				frm,
			});
		}, __("Create"));
	},
});
