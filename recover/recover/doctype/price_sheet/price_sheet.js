frappe.ui.form.on("Price Sheet", {
 refresh(frm) {
  if (frm.doc.docstatus === 1 && frappe.model.can_create("Quotation")) {
   frm.add_custom_button(__("Quotation"), () => {
    frappe.model.open_mapped_doc({
     method: "recover.recover.doctype.price_sheet.price_sheet.make_quotation",
     frm,
    });
   }, __("Create"));
  }
 },
});

frappe.ui.form.on("Price Sheet Item", {
 profit(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  frappe.model.set_value(cdt, cdn, "selling_price",
   flt(flt(row.total_cost) + flt(row.profit), precision("selling_price", row)));
  frm.set_value("total", (frm.doc.items || []).reduce(
   (total, item) => total + flt(item.qty) * flt(item.selling_price), 0));
 },
});
