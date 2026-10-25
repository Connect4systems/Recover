"""One-time migration for Cost Sheets created before workflow tracking."""


def execute():
    from recover.setup import setup_custom_fields
    from recover.cost_workflow import backfill_cost_sheet_statuses

    # Post-model-sync patches run before the after_migrate setup hook.
    setup_custom_fields()
    backfill_cost_sheet_statuses()
