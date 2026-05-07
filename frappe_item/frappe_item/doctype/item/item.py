import frappe
from frappe.utils import cint
from frappe import _

def validate_stock_exists_for_template_item(self):
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
