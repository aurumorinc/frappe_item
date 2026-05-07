import frappe

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
