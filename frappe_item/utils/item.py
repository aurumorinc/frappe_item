import frappe

def validate_attribute_values(doc, method=None):
    if not getattr(doc, "attributes", None):
        return

    # gather all attributes to check
    attr_names = list(set([d.attribute for d in doc.attributes if d.attribute]))
    if not attr_names:
        return

    # fetch numeric_values and valid values
    attributes_info = frappe.get_all("Item Attribute", filters={"name": ("in", attr_names)}, fields=["name", "numeric_values"])
    numeric_attr = {a.name for a in attributes_info if a.numeric_values}

    # for non-numeric, we need to get valid values
    non_numeric_attr = [a.name for a in attributes_info if not a.numeric_values]
    valid_values_map = {}
    if non_numeric_attr:
        valid_values_data = frappe.get_all("Item Attribute Value", filters={"parent": ("in", non_numeric_attr)}, fields=["parent", "attribute_value"])
        for d in valid_values_data:
            valid_values_map.setdefault(d.parent, set()).add(d.attribute_value)

    for d in doc.attributes:
        if not d.attribute or not getattr(d, "attribute_value", None):
            continue
            
        if d.attribute in numeric_attr:
            continue
            
        valid_vals = valid_values_map.get(d.attribute, set())
        
        # split by ; and check
        values = [v.strip() for v in d.attribute_value.split(";")]
        for val in values:
            if val and val not in valid_vals:
                frappe.throw(f"Invalid attribute value '{val}' for attribute '{d.attribute}'")

def copy_template_attribute_values(doc, method=None):
    """
    Singleton router for maintaining attribute consistency between Template and Variant items.
    """
    if doc.variant_of:
        # PULL Logic: Variant -> Pull from Template
        _pull_from_template(doc)
    elif doc.has_variants and method == "on_update":
        # PUSH Logic: Template -> Push to Variants
        # Only run on update to avoid propagation during initial template creation
        _push_to_variants(doc)

def _pull_from_template(doc):
    template = frappe.get_doc("Item", doc.variant_of)
    template_owned = {
        d.attribute: d.attribute_value 
        for d in template.attributes 
        if getattr(d, "attribute_value", None)
    }
    
    if not template_owned:
        return

    variant_attributes = {d.attribute: d for d in doc.attributes}
    for attr_name, value in template_owned.items():
        if attr_name in variant_attributes:
            if variant_attributes[attr_name].attribute_value != value:
                variant_attributes[attr_name].attribute_value = value
        else:
            doc.append("attributes", {
                "attribute": attr_name,
                "attribute_value": value
            })

def _push_to_variants(doc):
    variants = frappe.get_all("Item", filters={"variant_of": doc.name}, pluck="name")
    if not variants:
        return
        
    template_owned = {
        d.attribute: d.attribute_value 
        for d in doc.attributes 
        if getattr(d, "attribute_value", None)
    }
    
    if not template_owned:
        return
    
    for variant_name in variants:
        vdoc = frappe.get_doc("Item", variant_name)
        changed = False
        variant_attributes = {d.attribute: d for d in vdoc.attributes}
        
        for attr_name, value in template_owned.items():
            if attr_name in variant_attributes:
                row = variant_attributes[attr_name]
                if row.attribute_value != value:
                    row.attribute_value = value
                    changed = True
            else:
                vdoc.append("attributes", {
                    "attribute": attr_name,
                    "attribute_value": value
                })
                changed = True
        
        if changed:
            # Saving the variant will trigger its own before_save hook (pulling again),
            # ensuring full consistency across the chain.
            vdoc.save(ignore_permissions=True)
