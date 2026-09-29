## Recover

IT works and Equipment rent

#### License

mit
### Opportunity pricing workflow

1. Save an Opportunity and choose **Create > Price Request**. The request is linked to the opportunity; add the requested items directly in the Price Request.
2. Save the Price Request and choose **Create > Cost Sheet**. Item codes, names, descriptions, units, and quantities are copied separately. Purchase User and Purchase Manager can create and submit cost sheets.
3. Enter each item's unit **Price** and **Other Cost** in the opportunity currency. **Unit Total Cost = Price + Other Cost**. The sheet total sums quantity multiplied by unit total cost.
4. Select a supplier. Suppliers must be enabled and have the item's group in `Supplier.custom_item_group`. This field can be an Item Group link or a child table containing an Item Group link. Migration creates the table field if it does not already exist; populate it on your suppliers. The older `custom_supplier_item_group` field is not used by this workflow.
5. Submit the Cost Sheet. This automatically creates a draft **Price Sheet**, linked to the Cost Sheet and Opportunity, with Party Type, Party, and all cost items. It does not create a quotation.
6. A sales user enters **Unit Profit**, an amount rather than a percentage. **Unit Selling Price = Unit Total Cost + Unit Profit**. Source cost details remain read-only and are checked against the submitted Cost Sheet.
7. Submit the Price Sheet, then choose **Create > Quotation**. Review and save the quotation. It is linked to the opportunity and price sheet; every item's rate is its selling price, and its Cost (`custom_cost`) is the unit total cost.

After deploying the app, run:

```bash
bench --site <site> migrate
bench build --app recover
bench restart
```

Refresh the browser after restarting. Migration installs the new DocTypes and quotation links. Existing submitted cost sheets and quotations are not backfilled or replaced.

Run isolated controller checks with `python -m unittest discover -s tests -v`. A live Frappe/ERPNext site is required to verify document mapping, permissions, migration, and the full browser workflow.
