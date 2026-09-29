## Recover

IT works and Equipment rent

#### License

mit
### Opportunity pricing workflow

1. Save an Opportunity with items and choose **Create > Price Request**.
2. Save the Price Request and choose **Create > Cost Sheet**. Purchase User and Purchase Manager can create and submit cost sheets.
3. Enter each item's unit **Price** and **Other Cost** in the opportunity currency. **Total Cost = Price + Other Cost**; the sheet total sums quantity multiplied by unit total cost.
4. Submit the Cost Sheet to automatically create a draft Quotation linked to the sheet and opportunity. Each quotation item's **Cost** (`custom_cost`) receives its total unit cost. Selling rates come from the referenced opportunity items and remain separate from cost.

Item descriptions, UOMs, quantities, and opportunity row references carry through the workflow, including repeated item codes. Legacy price requests infer an opportunity row only when its item code has exactly one match.

After deploying the app, run `bench --site <site> migrate` and `bench build --app recover`, then restart your production processes as usual. The migration creates the quotation custom fields. Existing submitted cost sheets are not backfilled.

Run isolated controller checks with `python -m unittest discover -s tests -v`. A live Frappe/ERPNext site is required to verify document mapping, permissions, migration, and the full browser workflow.
