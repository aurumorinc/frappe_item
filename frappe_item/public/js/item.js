frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Wait for core scripts to execute, then unhide the column
        setTimeout(() => {
            if (frm.doc.has_variants && frm.doc.variant_based_on === "Item Attribute") {
                if (frm.fields_dict.attributes && frm.fields_dict.attributes.grid) {
                    frm.fields_dict.attributes.grid.set_column_disp("attribute_value", true);
                }
            }
        }, 100);
    }
});
