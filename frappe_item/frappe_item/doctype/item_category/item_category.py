# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.utils.nestedset import NestedSet


class ItemCategory(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.stock.doctype.item_default.item_default import ItemDefault
		from erpnext.stock.doctype.item_tax.item_tax import ItemTax
		from frappe.types import DF

		image: DF.AttachImage | None
		is_group: DF.Check
		item_category_defaults: DF.Table[ItemDefault]
		item_category_name: DF.Data
		lft: DF.Int
		old_parent: DF.Link | None
		parent_item_category: DF.Link | None
		rgt: DF.Int
		taxes: DF.Table[ItemTax]
	# end: auto-generated types
	pass
