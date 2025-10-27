# Copyright (c) 2024, AppXcess and contributors
# License: MIT

"""
Patch to add hierarchical sales roles to the CRM system.
This patch adds:
- Regional Sales Head
- Branch Sales Head
- Team Lead

These roles work alongside existing Sales User and Sales Manager roles.
"""

import frappe


def execute():
	"""Create new hierarchical roles if they don't exist."""
	
	roles_to_create = [
		{
			"role_name": "Regional Sales Head",
			"desk_access": 1,
			"is_custom": 0,
			"disabled": 0,
			"desk_access": 1
		},
		{
			"role_name": "Branch Sales Head",
			"desk_access": 1,
			"is_custom": 0,
			"disabled": 0,
			"desk_access": 1
		},
		{
			"role_name": "Team Lead",
			"desk_access": 1,
			"is_custom": 0,
			"disabled": 0,
			"desk_access": 1
		}
	]
	
	for role_data in roles_to_create:
		role_name = role_data.get("role_name")
		
		# Check if role already exists
		if frappe.db.exists("Role", role_name):
			frappe.logger().info(f"Role {role_name} already exists, skipping...")
			continue
		
		# Create the role
		try:
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				**{k: v for k, v in role_data.items() if k != "role_name"}
			})
			role_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.logger().info(f"Created role: {role_name}")
		except Exception as e:
			frappe.logger().error(f"Error creating role {role_name}: {str(e)}")
			continue
	
	frappe.msgprint("Hierarchical roles created successfully!")

