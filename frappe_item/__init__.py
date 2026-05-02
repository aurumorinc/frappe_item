__version__ = "0.0.1"

import frappe

def patch_make_variant_item_code():
    try:
        import erpnext.controllers.item_variant
        import erpnext.stock.doctype.item.item
        from frappe_item.overrides.item_variant import make_variant_item_code

        erpnext.controllers.item_variant.make_variant_item_code = make_variant_item_code
        erpnext.stock.doctype.item.item.make_variant_item_code = make_variant_item_code
    except ImportError:
        pass

patch_make_variant_item_code()
