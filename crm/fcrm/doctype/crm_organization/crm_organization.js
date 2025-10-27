// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// Modified for Education Center

frappe.ui.form.on("CRM Organization", {
	refresh(frm) {
		// Education-specific customizations
		// Add custom link if needed
		frm.add_web_link(`/crm/organizations/${frm.doc.name}`, __("Open in Portal"));
	},
	
	organization_name: function(frm) {
		// Auto-generate any related fields if needed
	},
	
	// Education-specific: Validate student count
	no_of_employees: function(frm) {
		// Can add validation for student count if needed
		if (frm.doc.no_of_employees) {
			// Validation logic can be added here
		}
	}
});
