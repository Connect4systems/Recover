"""Controller checks that run without a Frappe site: python -m unittest discover -s tests."""
import importlib
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


class Row(SimpleNamespace):
    def precision(self, field):
        return 2

    def get(self, field):
        return getattr(self, field, None)


def fail(message):
    raise ValueError(message)


class CostWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frappe = ModuleType("frappe")
        frappe.whitelist = lambda: lambda fn: fn
        frappe._ = lambda text: text
        frappe.throw = fail
        frappe.get_doc = Mock()
        frappe.new_doc = Mock()
        frappe.db = SimpleNamespace(exists=Mock(return_value=False))
        document = ModuleType("frappe.model.document")
        document.Document = object
        utils = ModuleType("frappe.utils")
        utils.flt = lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0)
        cls.modules = patch.dict(sys.modules, {"frappe": frappe, "frappe.model": ModuleType("frappe.model"), "frappe.model.document": document, "frappe.utils": utils})
        cls.modules.start()
        cls.controller = importlib.import_module("recover.recover.doctype.cost_sheet.cost_sheet")
        cls.frappe = frappe

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()

    def setUp(self):
        self.frappe.db.exists.reset_mock(return_value=True)
        self.frappe.db.exists.return_value = False
        self.sheet = self.controller.Costsheet()
        self.sheet.name = "COST-1"
        self.sheet.date = "2026-09-29"
        self.sheet.opportunity = None
        self.sheet.price_request = None
        self.sheet.precision = lambda field: 2
        self.sheet.items = [Row(item="ITEM-1", item_name="Item", qty=3, price=10, other_cost=2.5, total_cost=999, opportunity_item=None, description="Detail", uom="Nos")]

    def test_server_recalculates_cost_and_quantity_total(self):
        self.sheet.validate()
        self.assertEqual(self.sheet.items[0].total_cost, 12.5)
        self.assertEqual(self.sheet.total, 37.5)

    def test_empty_costs_are_zero(self):
        self.sheet.items[0].price = None
        self.sheet.items[0].other_cost = None
        self.sheet.validate()
        self.assertEqual(self.sheet.total, 0)

    def test_invalid_quantity_is_rejected(self):
        self.sheet.items[0].qty = 0
        with self.assertRaises(ValueError):
            self.sheet.validate()

    def test_mismatched_request_is_rejected(self):
        self.sheet.price_request = "PR-1"
        self.sheet.opportunity = "OPP-1"
        self.frappe.get_doc.return_value = Row(docstatus=0, opportunity="OPP-2", check_permission=Mock())
        with self.assertRaises(ValueError):
            self.sheet.validate()

    def test_foreign_opportunity_reference_is_rejected(self):
        self.sheet.opportunity = "OPP-1"
        self.sheet.items[0].opportunity_item = "OTHER-ROW"
        self.frappe.get_doc.return_value = Row(items=[Row(name="ROW-1", item_code="ITEM-1")])
        with self.assertRaises(ValueError):
            self.sheet.validate()

    def test_submission_preserves_duplicate_item_references_and_selling_rates(self):
        self.sheet.opportunity = "OPP-1"
        self.sheet.items[0].opportunity_item = "ROW-2"
        self.sheet.items.append(Row(item="ITEM-1", item_name="Item", qty=1, price=20, other_cost=3, total_cost=0, opportunity_item="ROW-1", description="First", uom="Nos"))
        self.frappe.get_doc.return_value = Row(name="OPP-1", opportunity_from="Customer", party_name="CUSTOMER", company="COMPANY", currency="EGP", items=[
            Row(name="ROW-1", item_code="ITEM-1", rate=100, description="First", uom="Nos"),
            Row(name="ROW-2", item_code="ITEM-1", rate=200, description="Second", uom="Nos"),
        ])
        quotation = Mock()
        self.frappe.new_doc.return_value = quotation
        self.sheet.validate()
        self.sheet.on_submit()
        first, second = [call.args[1] for call in quotation.append.call_args_list]
        self.assertEqual((first["custom_cost"], first["rate"], first["custom_opportunity_item"]), (12.5, 200, "ROW-2"))
        self.assertEqual((second["custom_cost"], second["rate"]), (23, 100))
        self.assertEqual(quotation.update.call_args.args[0]["opportunity"], "OPP-1")
        self.assertEqual(quotation.update.call_args.args[0]["custom_cost_sheet"], "COST-1")
        quotation.insert.assert_called_once_with(ignore_permissions=True)

    def test_existing_quotation_is_not_duplicated(self):
        self.sheet.opportunity = "OPP-1"
        self.frappe.db.exists.return_value = True
        self.frappe.new_doc.reset_mock()
        self.sheet.on_submit()
        self.frappe.new_doc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
