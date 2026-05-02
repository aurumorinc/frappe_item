import frappe

def after_migrate():
    # Automatically add custom fields to Item Variant Settings so they copy to variants
    add_variant_fields(["item_category", "item_tags"])

def add_variant_fields(fields_to_add):
    if not frappe.db.exists("DocType", "Item Variant Settings"):
        return
        
    settings = frappe.get_single("Item Variant Settings")
    existing_fields = [d.field_name for d in settings.get("fields", [])]
    
    changed = False
    
    for field in fields_to_add:
        if field not in existing_fields:
            settings.append("fields", {
                "field_name": field
            })
            changed = True
            
    if changed:
        settings.save(ignore_permissions=True)
        frappe.db.commit()
