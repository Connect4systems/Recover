frappe.ui.form.on("Opportunity", {
 refresh(frm) {
  if (!frm.is_new() && frm.doc.docstatus !== 2 && frappe.model.can_create("Price Request")) {
   frm.add_custom_button(__("Price Request"), () => {
    frappe.model.open_mapped_doc({
     method: "recover.recover.doctype.price_request.price_request.make_price_request",
     frm,
    });
   }, __("Create"));
  }
 },
});
