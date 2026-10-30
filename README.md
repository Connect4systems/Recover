## Recover

IT works and Equipment rent

#### License

mit
### Opportunity pricing workflow

1. Save an Opportunity and choose **Create > Price Request**. A new unsaved request opens, linked to the Opportunity, with all Opportunity item rows copied (item code, name, description, UOM, and quantity). Review and save the request. Rates are not copied. The Opportunity's Create menu hides **Supplier Quotation**, **Request For Quotation**, and **Quotation**, while preserving other entries, including **Select Item** supplied by the other app. The final quotation links to the Opportunity at document level.

2. Save the Price Request and choose **Create > Cost Sheet**. Item codes, names, descriptions, units, and quantities are copied separately. Purchase User and Purchase Manager can create and submit cost sheets.
3. Enter each item's unit **Price** and **Other Cost** in the opportunity currency. **Unit Total Cost = Price + Other Cost**. The sheet total sums quantity multiplied by unit total cost.
4. Select a supplier. Suppliers must be enabled and have the item's group in the `Supplier.custom_supplier_item_group` child table. The filter reads the table's Item Group link field, including the existing `item_greoup` field. Migration creates the supplier table field only if it is missing.
5. Submit the Cost Sheet. This automatically creates a draft **Price Sheet**, linked to the Cost Sheet and Opportunity, with Party Type, Party, and all cost items. It does not create a quotation.
   If linked to a Price Request, submission also applies that request's **Done** workflow action, moving **Pending Pricing** to **Pricing Complete** and submitting the request. The submitting user needs the workflow's **Purchase Manager** role and normal submission permissions. Already submitted requests in Pricing Complete are unchanged. Other request states or workflow/permission failures block Cost Sheet submission; the request, Cost Sheet, and Price Sheet changes share one transaction. This does not change the Cost Sheet's separate **Pending Price** status or automatically reopen requests when a Cost Sheet is cancelled.
6. A sales user enters **Unit Profit**, an amount rather than a percentage. **Unit Selling Price = Unit Total Cost + Unit Profit**. Source cost details remain read-only and are checked against the submitted Cost Sheet.
7. Submit the Price Sheet, then choose **Create > Quotation**. Review and save the quotation. It is linked to the opportunity and price sheet; every item's rate is its selling price, and its Cost (`custom_cost`) is the unit total cost.

The Cost Sheet's read-only **Status** follows this workflow:

The displayed document title includes its number and workflow status, for example **COST-26-10-01 - Pending Price** or **COST-26-10-01 - Sales Order - To Deliver and Bill**. Titles update with status changes. Migration fills titles on existing Cost Sheets without changing document numbers or links.

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

Cost Sheet **Connections > Purchasing** shows linked Material Requests and Purchase Orders, including drafts. Links follow the source Sales Order and Material Request references, support multiple documents per Cost Sheet and combined orders across Cost Sheets, and are backfilled during migration. These connections do not grant access to purchasing documents; standard Frappe permissions apply.

Run isolated controller checks with `python -m unittest discover -s tests -v`. A live Frappe/ERPNext site is required to verify document mapping, permissions, migration, and the full browser workflow.

### Opportunity Select Item (provided by the other app)

The existing **Create > Select Item** popup uses optional filters ordered **Category > Item Group > Brand**. Item Group choices are leaf groups (`is_group = 0`) linked through `Item Group.custom_category`. Allowed brands come from the selected Category's Brands child table (`Brand Table.brand`). Changing Category clears Item Group and Brand; changing any filter refreshes results and clears row selections.

Items are filtered through `Item.custom_category`, `Item.item_group`, and `Item.brand`; disabled items and variant templates are excluded. Results show 50 items per page with Select, Brand, Item Code, Item Name, Description, qty, and Item Image columns. Brand comes from the Item. The displayed qty sums `Bin.actual_qty` across accessible warehouses belonging to the Opportunity's company.

Pressing **Add** copies selected items into Opportunity Items with code, name, description, stock UOM, and quantity 1, skipping existing item codes. The popup closes so the user can review and save the Opportunity. It does not display, fetch, or set rates. This describes the supplied behavior of the other app; its implementation is not included in this repository.
