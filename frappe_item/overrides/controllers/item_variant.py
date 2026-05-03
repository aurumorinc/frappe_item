import copy
import frappe
from frappe.utils import cstr

def copy_attributes_to_variant(item, variant):
	# copy non no-copy fields

	exclude_fields = [
		"naming_series",
		"item_code",
		"item_name",
		"published_in_website",
		"opening_stock",
		"variant_of",
		"valuation_rate",
	]

	if item.variant_based_on == "Manufacturer":
		# don't copy manufacturer values if based on part no
		exclude_fields += ["manufacturer", "manufacturer_part_no"]

	allow_fields = [d.field_name for d in frappe.get_all("Variant Field", fields=["field_name"])]
	if "variant_based_on" not in allow_fields:
		allow_fields.append("variant_based_on")
	for field in item.meta.fields:
		# "Table" is part of `no_value_field` but we shouldn't ignore tables
		if (field.reqd or field.fieldname in allow_fields) and field.fieldname not in exclude_fields:
			if variant.get(field.fieldname) != item.get(field.fieldname):
				if field.fieldtype in ("Table", "Table MultiSelect"):
					variant.set(field.fieldname, [])
					for d in item.get(field.fieldname):
						row = copy.deepcopy(d)
						if row.get("name"):
							row.name = None
						variant.append(field.fieldname, row)
				else:
					variant.set(field.fieldname, item.get(field.fieldname))

	variant.variant_of = item.name

	if "description" not in allow_fields:
		if not variant.description:
			variant.description = ""
	else:
		if item.variant_based_on == "Item Attribute":
			if variant.attributes:
				attributes_description = item.description or ""
				for d in variant.attributes:
					attributes_description += (
						"<div>" + d.attribute + ": " + cstr(d.attribute_value) + "</div>"
					)

				if attributes_description not in (variant.description or ""):
					variant.description = attributes_description

def make_variant_item_code(template_item_code, template_item_name, variant):
	"""Uses template's item code and abbreviations to make variant's item code"""
	if variant.item_code:
		return

	# Fetch the template to check which attributes should be included
	template = frappe.get_doc("Item", variant.variant_of)
	include_map = {d.attribute: d.include_in_item_code for d in template.attributes}

	abbreviations = []
	for attr in variant.attributes:
		# Skip if explicitly excluded in the template
		if not include_map.get(attr.attribute, 1):
			continue

		item_attribute = frappe.db.sql(
			"""select i.numeric_values, v.abbr
			from `tabItem Attribute` i left join `tabItem Attribute Value` v
				on (i.name=v.parent)
			where i.name=%(attribute)s and (v.attribute_value=%(attribute_value)s or i.numeric_values = 1)""",
			{"attribute": attr.attribute, "attribute_value": attr.attribute_value},
			as_dict=True,
		)

		if not item_attribute:
			continue

		abbr_or_value = (
			cstr(attr.attribute_value) if item_attribute[0].numeric_values else item_attribute[0].abbr
		)
		abbreviations.append(abbr_or_value)

	if abbreviations:
		variant.item_code = "{}-{}".format(template_item_code, "-".join(abbreviations))
		variant.item_name = "{}-{}".format(template_item_name, "-".join(abbreviations))
