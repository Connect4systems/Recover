## Recover

IT works and Equipment rent

#### License

mit
### Opportunity pricing workflow

1. Save an Opportunity and choose **Create > Price Request**. The request is linked to the opportunity; add the requested items directly in the Price Request.
Items originate in the Price Request. No opportunity item rows or opportunity-item references are required at any stage; the final quotation links to the Opportunity at document level.

2. Save the Price Request and choose **Create > Cost Sheet**. Item codes, names, descriptions, units, and quantities are copied separately. Purchase User and Purchase Manager can create and submit cost sheets.
3. Enter each item's unit **Price** and **Other Cost** in the opportunity currency. **Unit Total Cost = Price + Other Cost**. The sheet total sums quantity multiplied by unit total cost.
4. Select a supplier. Suppliers must be enabled and have the item's group in the `Supplier.custom_supplier_item_group` child table. The filter reads the table's Item Group link field, including the existing `item_greoup` field. Migration creates the supplier table field only if it is missing.
5. Submit the Cost Sheet. This automatically creates a draft **Price Sheet**, linked to the Cost Sheet and Opportunity, with Party Type, Party, and all cost items. It does not create a quotation.
6. A sales user enters **Unit Profit**, an amount rather than a percentage. **Unit Selling Price = Unit Total Cost + Unit Profit**. Source cost details remain read-only and are checked against the submitted Cost Sheet.
7. Submit the Price Sheet, then choose **Create > Quotation**. Review and save the quotation. It is linked to the opportunity and price sheet; every item's rate is its selling price, and its Cost (`custom_cost`) is the unit total cost.

The Cost Sheet's read-only **Status** follows this workflow:

- Submitting the Cost Sheet creates the draft Price Sheet and sets **Pending Price**.
- Submitting the Price Sheet sets **Price Complete**.
- Saving a linked quotation sets **Quotation - [Status]**.
- Saving a Sales Order made from that quotation sets **Sales Order - [Status]**.
- Submitting that Sales Order automatically creates a draft **Purchase Material Request** using ERPNext's standard Sales Order mapping. It retains the source Sales Order and item references; repeat events reuse the existing active request. Purchasing reviews and submits the request before issuing a PO.
- Submitting a Purchase Order against that Material Request sets **PO - [Status]**.

Later status changes, including cancellation, update the current stage. Delivery, receipt, and invoice submission/cancellation refresh order statuses too. Earlier stages cannot overwrite a later stage; cancelled Cost Sheets are ignored. If several documents exist at the same stage, the latest processed event supplies the displayed status. Orders combining multiple source quotations update all originating Cost Sheets; the Material Request link on each Cost Sheet shows its most recently created request. Existing submitted Cost Sheet statuses are backfilled during migration as described below.

After deploying the app, run:

```bash
bench --site <site> migrate
bench build --app recover
bench restart
```

Refresh the browser after restarting. Migration installs the new DocTypes and quotation links. A one-time migration updates existing submitted Cost Sheet statuses from linked Price Sheets, Quotations, Sales Orders, and issued Purchase Orders. It uses explicit document references, preserves later workflow stages, and processes the latest modified document last within each stage. It does not create historical Material Requests or replace documents. Draft and cancelled Cost Sheets are unchanged.

To rerun status backfilling explicitly: `bench --site <site> execute recover.cost_workflow.backfill_cost_sheet_statuses`.

Run isolated controller checks with `python -m unittest discover -s tests -v`. A live Frappe/ERPNext site is required to verify document mapping, permissions, migration, and the full browser workflow.
