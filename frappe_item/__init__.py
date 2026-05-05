__version__ = "0.0.1"

import frappe

def patch_item_variant():
    try:
        import erpnext.controllers.item_variant
        import erpnext.stock.doctype.item.item
        from frappe_item.overrides.controllers.item_variant import make_variant_item_code, copy_attributes_to_variant

        erpnext.controllers.item_variant.make_variant_item_code = make_variant_item_code
        erpnext.stock.doctype.item.item.make_variant_item_code = make_variant_item_code
        erpnext.controllers.item_variant.copy_attributes_to_variant = copy_attributes_to_variant
        erpnext.stock.doctype.item.item.copy_attributes_to_variant = copy_attributes_to_variant
    except ImportError:
        pass

patch_item_variant()
