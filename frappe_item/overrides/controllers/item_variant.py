import frappe
from frappe.utils import cstr

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
