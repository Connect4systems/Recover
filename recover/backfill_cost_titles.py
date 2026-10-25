"""Populate display titles after the title field has been installed."""


def execute():
    from recover.cost_workflow import backfill_cost_sheet_titles

    backfill_cost_sheet_titles()
