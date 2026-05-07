import frappe
from frappe.tests import IntegrationTestCase

class TestItemAttributesSync(IntegrationTestCase):
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
        # Create an Item Group
        if not frappe.db.exists("Item Group", "_Test Item Group"):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": "_Test Item Group",
                "is_group": 0,
            }).insert()

        # Ensure HSN Code exists for India Compliance
        if not frappe.db.exists("GST HSN Code", "9999"):
            frappe.get_doc({
                "doctype": "GST HSN Code",
                "name": "9999",
                "description": "Test HSN"
            }).insert(ignore_permissions=True)

        # Create Item Attributes
        for attr in ["Test Size", "Test Material", "Test Sleeve"]:
            if not frappe.db.exists("Item Attribute", attr):
                values = []
                if attr == "Test Size":
                    values = [{"attribute_value": "Small", "abbr": "S"}, {"attribute_value": "Large", "abbr": "L"}]
                elif attr == "Test Material":
                    values = [{"attribute_value": "Cotton", "abbr": "C"}, {"attribute_value": "Polyester", "abbr": "P"}, {"attribute_value": "Silk", "abbr": "Si"}]
                elif attr == "Test Sleeve":
                    values = [{"attribute_value": "Short", "abbr": "Sh"}, {"attribute_value": "Long", "abbr": "Lo"}]
                
                frappe.get_doc({
                    "doctype": "Item Attribute",
                    "attribute_name": attr,
                    "item_attribute_values": values
                }).insert()

    def _create_template(self, item_code):
        if not frappe.db.exists("Item", item_code):
            return frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_group": "_Test Item Group",
                "stock_uom": "Nos",
                "is_stock_item": 1,
                "has_variants": 1,
                "variant_based_on": "Item Attribute",
                "gst_hsn_code": "9999",
                "attributes": [
                    {"attribute": "Test Size"}, # Variant-owned
                    {"attribute": "Test Material", "attribute_value": "Cotton"} # Template-owned
                ]
            }).insert()
        return frappe.get_doc("Item", item_code)

    def test_variant_pulls_owned_attributes_on_save(self):
        template_name = "TEST-TEMPLATE-PULL"
        variant_name = "TEST-VARIANT-PULL"
        
        self._create_template(template_name)

        if frappe.db.exists("Item", variant_name):
            frappe.delete_doc("Item", variant_name)

        # Create a variant
        variant = frappe.get_doc({
            "doctype": "Item",
            "item_code": variant_name,
            "item_group": "_Test Item Group",
            "stock_uom": "Nos",
            "gst_hsn_code": "9999",
            "variant_of": template_name,
            "attributes": [
                {"attribute": "Test Size", "attribute_value": "Small"}
            ]
        }).insert()

        # Verify "Test Material" was pulled from template during insert
        variant.reload()
        attr_values = {d.attribute: d.attribute_value for d in variant.attributes}
        
        self.assertIn("Test Material", attr_values)
        self.assertEqual(attr_values["Test Material"], "Cotton")
        self.assertEqual(attr_values["Test Size"], "Small")

    def test_template_pushes_updates_to_variants(self):
        template_name = "TEST-TEMPLATE-PUSH"
        variant_name = "TEST-VARIANT-PUSH"
        
        template = self._create_template(template_name)

        if frappe.db.exists("Item", variant_name):
            frappe.delete_doc("Item", variant_name)

        # Create variant and save it to DB
        variant = frappe.get_doc({
            "doctype": "Item",
            "item_code": variant_name,
            "item_group": "_Test Item Group",
            "stock_uom": "Nos",
            "gst_hsn_code": "9999",
            "variant_of": template_name,
            "attributes": [
                {"attribute": "Test Size", "attribute_value": "Large"}
            ]
        }).insert()

        # Update Template: Change existing and add new
        for attr in template.attributes:
            if attr.attribute == "Test Material":
                attr.attribute_value = "Polyester"

        template.append("attributes", {
            "attribute": "Test Sleeve",
            "attribute_value": "Short"
        })
        
        template.save() # Triggers on_update hook

        # Reload variant and verify
        variant.reload()
        attr_values = {d.attribute: d.attribute_value for d in variant.attributes}
        
        self.assertEqual(attr_values.get("Test Material"), "Polyester")
        self.assertEqual(attr_values.get("Test Sleeve"), "Short")
        self.assertEqual(attr_values.get("Test Size"), "Large") # Still preserved

    def test_intelligent_ownership_preservation(self):
        template_name = "TEST-TEMPLATE-OWNER"
        variant_name = "TEST-VARIANT-OWNER"
        
        self._create_template(template_name)

        if frappe.db.exists("Item", variant_name):
            frappe.delete_doc("Item", variant_name)

        # Attempt to create variant with an incorrect value for a template-owned attribute
        variant = frappe.get_doc({
            "doctype": "Item",
            "item_code": variant_name,
            "item_group": "_Test Item Group",
            "stock_uom": "Nos",
            "gst_hsn_code": "9999",
            "variant_of": template_name,
            "attributes": [
                {"attribute": "Test Size", "attribute_value": "Small"},
                {"attribute": "Test Material", "attribute_value": "Silk"} # Manually set wrong value
            ]
        }).insert()

        variant.reload()
        attr_values = {d.attribute: d.attribute_value for d in variant.attributes}
        
        self.assertEqual(attr_values.get("Test Size"), "Small")
        # Template owns "Test Material" (set to "Cotton"), so "Silk" SHOULD be overwritten
        self.assertEqual(attr_values.get("Test Material"), "Cotton")
