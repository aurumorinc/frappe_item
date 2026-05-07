__version__ = "0.0.1"

import frappe
from frappe.utils import cint
from frappe import _

def validate_stock_exists_for_template_item_patched(self):
    from erpnext.stock.doctype.item.item import StockExistsForTemplate
    
    if self.stock_ledger_created() and self._doc_before_save:
        if (
            cint(self._doc_before_save.has_variants) != cint(self.has_variants)
            or self._doc_before_save.variant_of != self.variant_of
        ):
            frappe.throw(
                _(
                    "Cannot change Variant properties after stock transaction. You will have to make a new Item to do this."
                ).format(self.name),
                StockExistsForTemplate,
            )

        # Removed the attributes check to allow changes even after stock transactions.

def patch_item_variant():
    try:
        import erpnext.controllers.item_variant
        import erpnext.stock.doctype.item.item
        from frappe_item.overrides.controllers.item_variant import make_variant_item_code, copy_attributes_to_variant

        erpnext.controllers.item_variant.make_variant_item_code = make_variant_item_code
        erpnext.stock.doctype.item.item.make_variant_item_code = make_variant_item_code
        erpnext.controllers.item_variant.copy_attributes_to_variant = copy_attributes_to_variant
        erpnext.stock.doctype.item.item.copy_attributes_to_variant = copy_attributes_to_variant
        
        # Monkey patch validate_stock_exists_for_template_item
        erpnext.stock.doctype.item.item.Item.validate_stock_exists_for_template_item = validate_stock_exists_for_template_item_patched
    except ImportError:
        pass

patch_item_variant()
