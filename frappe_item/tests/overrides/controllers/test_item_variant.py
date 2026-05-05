import frappe
from frappe.tests.utils import FrappeTestCase

class TestItemVariant(FrappeTestCase):
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

        # Create Item Attribute
        if not frappe.db.exists("Item Attribute", "Test Size"):
            frappe.get_doc({
                "doctype": "Item Attribute",
                "attribute_name": "Test Size",
                "item_attribute_values": [
                    {"attribute_value": "S", "abbr": "S"},
                    {"attribute_value": "M", "abbr": "M"},
                ]
            }).insert()
            
        # Create some Item Tags
        for tag in ["Tag 1", "Tag 2"]:
            if not frappe.db.exists("Item Tag", tag):
                frappe.get_doc({"doctype": "Item Tag", "name": tag}).insert()
                
        # Ensure item_tags is in Variant Field
        variant_settings = frappe.get_doc("Item Variant Settings")
        allow_fields = [d.field_name for d in variant_settings.get("fields", [])]
        if "item_tags" not in allow_fields:
            variant_settings.append("fields", {"field_name": "item_tags"})
            variant_settings.save()
            
        # Ensure HSN Code exists for India Compliance
        if not frappe.db.exists("GST HSN Code", "9999"):
            frappe.get_doc({
                "doctype": "GST HSN Code",
                "name": "61091000",
                "description": "Test HSN"
            }).insert(ignore_permissions=True)

        # Create a Template Item
        if not frappe.db.exists("Item", "Test-Template-Tags"):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test-Template-Tags",
                "item_group": "_Test Item Group",
                "stock_uom": "Nos",
                "is_stock_item": 1,
                "has_variants": 1,
                "variant_based_on": "Item Attribute",
                "gst_hsn_code": "9999",
                "attributes": [{"attribute": "Test Size"}],
            }).insert()

    def test_template_retains_tags_on_save(self):
        # Retrieve the template
        template = frappe.get_doc("Item", "Test-Template-Tags")
        
        # We need a variant to trigger `update_variants`
        if not frappe.db.exists("Item", "Test-Template-Tags-S"):
            variant = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test-Template-Tags-S",
                "variant_of": "Test-Template-Tags",
                "item_group": "_Test Item Group",
                "stock_uom": "Nos",
                "gst_hsn_code": "9999",
                "attributes": [{"attribute": "Test Size", "attribute_value": "S"}],
            }).insert()

        # Add tags to the template
        template.set("item_tags", [])
        template.append("item_tags", {"item_tag": "Tag 1"})
        template.append("item_tags", {"item_tag": "Tag 2"})
        template.save()
        
        # Reload and verify template still has 2 tags
        template.reload()
        self.assertEqual(len(template.item_tags), 2, "Template lost its tags after save!")
        
        # Verify the variant inherited the tags correctly as copies
        variant = frappe.get_doc("Item", "Test-Template-Tags-S")
        self.assertEqual(len(variant.item_tags), 2, "Variant didn't receive tags!")
        
        # Ensure the row names are different (they are deep copies)
        template_tag_names = [t.name for t in template.item_tags]
        variant_tag_names = [v.name for v in variant.item_tags]
        for v_name in variant_tag_names:
            self.assertNotIn(v_name, template_tag_names, "Variant stole the child row from Template!")
