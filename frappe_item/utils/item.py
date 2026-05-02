import frappe

def copy_template_attribute_values(doc, method):
    # Only run this logic for Variant Items
    if not doc.variant_of:
        return
        
    # Fetch the Template Item
    template = frappe.get_doc("Item", doc.variant_of)
    
    # Map all attributes on the Template that actually have a value
    template_attr_values = {
        d.attribute: d.attribute_value 
        for d in template.attributes 
        if getattr(d, "attribute_value", None)
    }
    
    # Inject those values into the Variant's empty attribute rows
    for row in doc.attributes:
        # If the variant row has no value, but the template did, copy it over!
        if not getattr(row, "attribute_value", None) and row.attribute in template_attr_values:
            row.attribute_value = template_attr_values[row.attribute]

