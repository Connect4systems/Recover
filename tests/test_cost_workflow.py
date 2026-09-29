"""Controller checks that run without a Frappe site: python -m unittest discover -s tests."""
import importlib
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


class Row(SimpleNamespace):
    def precision(self, field):
        return 2

    def set(self, field, value):
        setattr(self, field, value)

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
        frappe.db = SimpleNamespace(exists=Mock(return_value=False), get_value=Mock(return_value=1))
        frappe.get_cached_value = Mock(return_value="Equipment")
        frappe.get_meta = Mock()
        frappe.get_all = Mock(return_value=["SUP-1"])
        frappe.has_permission = Mock()
        mapper = ModuleType("frappe.model.mapper")
        mapper.get_mapped_doc = Mock()
        document = ModuleType("frappe.model.document")
        document.Document = object
        utils = ModuleType("frappe.utils")
        utils.flt = lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0)
        cls.modules = patch.dict(sys.modules, {"frappe": frappe, "frappe.model": ModuleType("frappe.model"), "frappe.model.document": document, "frappe.utils": utils, "frappe.model.mapper": mapper})
        cls.modules.start()
        cls.controller = importlib.import_module("recover.recover.doctype.cost_sheet.cost_sheet")
        cls.pricing = importlib.import_module("recover.recover.doctype.price_sheet.price_sheet")
        cls.requests = importlib.import_module("recover.recover.doctype.price_request.price_request")
        cls.mapper = mapper
        cls.frappe = frappe

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()

    def setUp(self):
        self.frappe.get_doc.side_effect = None
        self.frappe.db.exists.reset_mock(return_value=True)
        self.frappe.db.exists.return_value = False
        self.sheet = self.controller.Costsheet()
        self.sheet.name = "COST-1"
        self.sheet.date = "2026-09-29"
        self.sheet.opportunity = None
        self.sheet.price_request = None
        self.sheet.precision = lambda field: 2
        self.sheet.items = [Row(name="COST-ROW-1", supplier=None, item="ITEM-1", item_name="Item", qty=3, price=10, other_cost=2.5, total_cost=999, description="Detail", uom="Nos")]

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

    def test_cost_mapping_needs_no_opportunity_item_fields(self):
        self.requests.make_cost_sheet("PR-1")
        populate = self.mapper.get_mapped_doc.call_args.args[4]
        source = Row(docstatus=0, opportunity="OPP-1")
        target = Row(items=[Row(item="CODE-001", item_name="Display name")])
        self.frappe.get_doc.return_value = Row(opportunity_from="Customer", party_name="CUSTOMER")
        populate(source, target)
        self.assertEqual(target.items[0].item, "CODE-001")
        self.assertEqual(target.party, "CUSTOMER")
        self.assertFalse(hasattr(target.items[0], "opportunity_item"))

    def test_price_request_validation_needs_no_opportunity_items(self):
        request = self.requests.PriceRequest()
        request.opportunity = "OPP-1"
        request.items = [Row(item="CODE-001")]
        self.frappe.get_doc.return_value = Row(opportunity_from="Customer", party_name="CUSTOMER")
        request.validate()
        self.assertEqual(request.party, "CUSTOMER")

    def test_submission_creates_price_sheet_without_opportunity_items(self):
        self.sheet.opportunity = "OPP-1"
        self.frappe.get_doc.return_value = Row(name="OPP-1", opportunity_from="Customer", party_name="CUSTOMER")
        price_sheet = Mock()
        self.frappe.new_doc.return_value = price_sheet
        self.sheet.validate()
        self.sheet.on_submit()
        self.frappe.new_doc.assert_called_with("Price Sheet")
        values = price_sheet.append.call_args.args[1]
        self.assertEqual((values["item"], values["total_cost"], values["selling_price"]), ("ITEM-1", 12.5, 12.5))
        self.assertEqual(values["cost_sheet_item"], "COST-ROW-1")
        self.assertEqual(price_sheet.update.call_args.args[0]["cost_sheet"], "COST-1")
        price_sheet.insert.assert_called_once_with(ignore_permissions=True)

    def test_existing_price_sheet_is_not_duplicated(self):
        self.sheet.opportunity = "OPP-1"
        self.frappe.db.exists.return_value = True
        self.frappe.new_doc.reset_mock()
        self.sheet.on_submit()
        self.frappe.new_doc.assert_not_called()

    def test_supplier_filter_uses_custom_item_group_table(self):
        supplier_meta = Mock()
        supplier_meta.get_field.return_value = Row(fieldtype="Table", options="Supplier Item Group")
        child_meta = Row(fields=[Row(fieldname="item_greoup", fieldtype="Link", options="Item Group")])
        self.frappe.get_meta.side_effect = lambda dt: supplier_meta if dt == "Supplier" else child_meta
        self.assertEqual(self.controller.get_item_group_suppliers("Equipment"), ["SUP-1"])
        self.assertEqual(self.frappe.get_all.call_args.kwargs["filters"], {"item_greoup": "Equipment", "parenttype": "Supplier", "parentfield": "custom_item_group"})

    def test_supplier_filter_supports_direct_item_group_link(self):
        meta = Mock()
        meta.get_field.return_value = Row(fieldtype="Link", options="Item Group")
        self.frappe.get_meta.side_effect = None
        self.frappe.get_meta.return_value = meta
        self.controller.get_item_group_suppliers("Equipment")
        self.assertEqual(self.frappe.get_all.call_args.kwargs["filters"], {"custom_item_group": "Equipment"})

    def test_item_code_is_explicitly_mapped_separately_from_name(self):
        self.requests.make_cost_sheet("PR-1")
        mapping = self.mapper.get_mapped_doc.call_args.args[2]["Pricing Items"]["field_map"]
        source = {"name": "REQUEST-ROW", "item": "CODE-001", "item_name": "Display name", "description": "Detail", "uom": "Nos", "qty": 2}
        target = {target: source[field] for field, target in mapping.items()}
        self.assertEqual(target["item"], "CODE-001")
        self.assertEqual(target["item_name"], "Display name")

    def make_price_sheet(self):
        sheet = self.pricing.PriceSheet()
        sheet.name = "PS-1"
        sheet.docstatus = 1
        sheet.cost_sheet = "COST-1"
        sheet.opportunity = "OPP-1"
        sheet.party_type = "Customer"
        sheet.party = "CUSTOMER"
        sheet.precision = lambda field: 2
        sheet.check_permission = Mock()
        sheet.items = [Row(cost_sheet_item="COST-ROW-1", profit=5)]
        self.sheet.docstatus = 1
        self.sheet.opportunity = "OPP-1"
        self.sheet.items[0].total_cost = 12.5
        opportunity = Row(name="OPP-1", opportunity_from="Customer", party_name="CUSTOMER", company="COMPANY", currency="EGP")
        self.frappe.get_doc.side_effect = lambda dt, name: {"Cost sheet": self.sheet, "Opportunity": opportunity, "Price Sheet": sheet}[dt]
        return sheet

    def test_selling_price_uses_profit_amount_and_source_cost(self):
        sheet = self.make_price_sheet()
        sheet.validate()
        self.assertEqual(sheet.items[0].selling_price, 17.5)
        self.assertEqual(sheet.total, 52.5)
        self.assertEqual(sheet.items[0].item, "ITEM-1")

    def test_price_sheet_rejects_missing_source_items(self):
        sheet = self.make_price_sheet()
        sheet.items = []
        with self.assertRaises(ValueError):
            sheet.validate()

    def test_price_sheet_requires_submitted_cost_sheet(self):
        sheet = self.make_price_sheet()
        self.sheet.docstatus = 0
        with self.assertRaises(ValueError):
            sheet.validate()

    def test_quotation_uses_selling_price_and_links(self):
        sheet = self.make_price_sheet()
        sheet.validate()
        quotation = Mock()
        self.frappe.new_doc.return_value = quotation
        quotation.items = [Row(rate=0)]
        self.pricing.make_quotation("PS-1")
        self.assertEqual(quotation.items[0].rate, 17.5)
        values = quotation.append.call_args.args[1]
        self.assertEqual((values["item_code"], values["rate"], values["custom_cost"]), ("ITEM-1", 17.5, 12.5))
        header = quotation.update.call_args.args[0]
        self.assertEqual((header["opportunity"], header["custom_price_sheet"]), ("OPP-1", "PS-1"))
        quotation.insert.assert_not_called()

    def test_draft_price_sheet_cannot_create_quotation(self):
        sheet = self.make_price_sheet()
        sheet.docstatus = 0
        with self.assertRaises(ValueError):
            self.pricing.make_quotation("PS-1")


if __name__ == "__main__":
    unittest.main()
