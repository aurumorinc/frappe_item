import frappe
from frappe.tests import IntegrationTestCase
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

class TestItemMonkeyPatch(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_test_records()

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    @classmethod
    def create_test_records(cls):
        if not frappe.db.exists("Item Group", "_Test Item Group"):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": "_Test Item Group",
                "is_group": 0,
            }).insert()

        if not frappe.db.exists("GST HSN Code", "9999"):
            frappe.get_doc({
                "doctype": "GST HSN Code",
                "name": "9999",
                "description": "Test HSN"
            }).insert(ignore_permissions=True)

        for attr in ["Test Size 2", "Test Material 2"]:
            if not frappe.db.exists("Item Attribute", attr):
                values = []
                if attr == "Test Size 2":
                    values = [{"attribute_value": "Small", "abbr": "S"}, {"attribute_value": "Large", "abbr": "L"}]
                elif attr == "Test Material 2":
                    values = [{"attribute_value": "Cotton", "abbr": "C"}, {"attribute_value": "Polyester", "abbr": "P"}]
                
                frappe.get_doc({
                    "doctype": "Item Attribute",
                    "attribute_name": attr,
                    "item_attribute_values": values
                }).insert()

    def test_allow_attribute_change_after_stock_transaction(self):
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        template_name = f"TEST-TEMPLATE-STOCK-{unique_id}"
        variant_name = f"TEST-VARIANT-STOCK-{unique_id}"

        # Create template
        template = frappe.get_doc({
            "doctype": "Item",
            "item_code": template_name,
            "item_group": "_Test Item Group",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "has_variants": 1,
            "variant_based_on": "Item Attribute",
            "gst_hsn_code": "9999",
            "attributes": [
                {"attribute": "Test Size 2"},
            ]
        }).insert()

        # Create a variant
        variant = frappe.get_doc({
            "doctype": "Item",
            "item_code": variant_name,
            "item_group": "_Test Item Group",
            "stock_uom": "Nos",
            "gst_hsn_code": "9999",
            "variant_of": template_name,
            "attributes": [
                {"attribute": "Test Size 2", "attribute_value": "Small"}
            ]
        }).insert()

        # Add stock to the variant
        company = frappe.db.get_value("Company", filters={})
        warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0})

        if not warehouse:
            if not company:
                company_doc = frappe.get_doc({
                    "doctype": "Company",
                    "company_name": "_Test Company",
                    "default_currency": "INR",
                    "abbr": "_TC"
                }).insert()
                company = company_doc.name
            warehouse_doc = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": "_Test Warehouse",
                "company": company
            }).insert()
            warehouse = warehouse_doc.name

        se = make_stock_entry(
            item_code=variant.name,
            qty=10,
            to_warehouse=warehouse,
            rate=100,
            company=company
        )

        # Clear cache to ensure it fetches updated count
        frappe.db.commit()
        variant.reload()

        if hasattr(variant, '_stock_ledger_created'):
            delattr(variant, '_stock_ledger_created')

        # Confirm stock ledger entry exists
        self.assertTrue(variant.stock_ledger_created())

        # Attempt to change attributes on the variant (this would normally fail)
        variant.append("attributes", {"attribute": "Test Material 2", "attribute_value": "Cotton"})
        
        try:
            variant.save()
        except Exception as e:
            self.fail(f"Saving variant with modified attributes after stock transaction failed: {e}")

        # Attempt to change attributes on the template
        template.reload()
        template.append("attributes", {"attribute": "Test Material 2"})
        try:
            template.save()
        except Exception as e:
            self.fail(f"Saving template with modified attributes after stock transaction failed: {e}")
