frappe.ui.form.on("Price Sheet", {
 on_submit(frm) {
  if (frm.doc.quotation) {
   frappe.set_route("Form", "Quotation", frm.doc.quotation);
  }
 },
});

frappe.ui.form.on("Price Sheet Item", {
 profit(frm, cdt, cdn) {
  return update_price_sheet_row(frm, cdt, cdn);
 },
 other_cost(frm, cdt, cdn) {
  return update_price_sheet_row(frm, cdt, cdn);
 },
});

async function update_price_sheet_row(frm, cdt, cdn) {
 const row = locals[cdt][cdn];
 const total_cost = flt(flt(row.price) + flt(row.other_cost), precision("total_cost", row));
 await frappe.model.set_value(cdt, cdn, {
  total_cost,
  selling_price: flt(total_cost + flt(row.profit), precision("selling_price", row)),
 });
 await frm.set_value("total", (frm.doc.items || []).reduce(
  (total, item) => total + flt(item.qty) * flt(item.selling_price), 0));
}
