import frappe
from crm.utils.territory_hierarchy import (
	get_user_role_hierarchy,
	can_user_manage_role,
	ROLE_HIERARCHY
)


@frappe.whitelist()
def add_existing_users(users, role="Sales User"):
	"""
	Add existing users to the CRM by assigning them a role.
	Supports: Sales User, Team Lead, Branch Sales Head, Regional Sales Head, Sales Manager, System Manager
	:param users: List of user names to be added
	"""
	# Check current user can manage this role
	current_role, _ = get_user_role_hierarchy()
	allowed_roles = ["System Manager", "Sales Manager", "Regional Sales Head", "Branch Sales Head"]
	
	if current_role not in allowed_roles:
		frappe.only_for(["System Manager", "Sales Manager"])
	
	if not can_user_manage_role(current_role, role):
		frappe.throw(f"Insufficient permissions to assign role: {role}")
	
	users = frappe.parse_json(users)

	for user in users:
		add_user(user, role)


@frappe.whitelist()
def update_user_role(user, new_role):
	"""
	Update the role of the user to Sales Manager, Sales User, System Manager, or hierarchical roles.
	Supports: Sales User, Team Lead, Branch Sales Head, Regional Sales Head, Sales Manager, System Manager
	:param user: The name of the user
	:param new_role: The new role to assign
	"""

	# Check permissions - use hierarchy to determine who can assign what
	current_role, _ = get_user_role_hierarchy()
	allowed_roles = ["System Manager", "Sales Manager", "Regional Sales Head", "Branch Sales Head"]
	
	if current_role not in allowed_roles:
		frappe.only_for(["System Manager", "Sales Manager"])
	
	# Check if current user can manage this role
	if current_role and not can_user_manage_role(current_role, new_role):
		frappe.throw(f"Insufficient permissions to assign role: {new_role}")

	# Get hierarchy for the new role
	hierarchy = ROLE_HIERARCHY.get(new_role, {})
	
	# List of all CRM roles (for removing)
	all_crm_roles = ["System Manager", "Sales Manager", "Regional Sales Head", 
	                  "Branch Sales Head", "Team Lead", "Sales User"]

	user_doc = frappe.get_doc("User", user)

	# Remove all CRM roles first
	for role in all_crm_roles:
		user_doc.remove_roles(role)

	# Add roles based on hierarchy
	roles_to_add = hierarchy.get("can_manage_roles", [])
	if not roles_to_add:
		# Fallback for roles not in hierarchy (backward compatibility)
		if new_role == "System Manager":
			roles_to_add = ["System Manager", "Sales Manager", "Sales User"]
		elif new_role == "Sales Manager":
			roles_to_add = ["Sales Manager", "Sales User"]
		elif new_role == "Sales User":
			roles_to_add = ["Sales User"]
		else:
			roles_to_add = [new_role, "Sales User"]
	
	user_doc.append_roles(*roles_to_add)

	# System Manager gets all modules
	if new_role == "System Manager":
		user_doc.set("block_modules", [])
	else:
		# Restrict to FCRM for all other roles
		update_module_in_user(user_doc, "FCRM")

	user_doc.save(ignore_permissions=True)


@frappe.whitelist()
def add_user(user, role):
	"""
	Add a user means adding role (Sales User or/and Sales Manager) to the user.
	:param user: The name of the user to be added
	:param role: The role to be assigned (Sales User or Sales Manager)
	"""
	update_user_role(user, role)


@frappe.whitelist()
def remove_user(user):
	"""
	Remove a user means removing all CRM roles from the user.
	Supports: Sales User, Team Lead, Branch Sales Head, Regional Sales Head, Sales Manager, System Manager
	:param user: The name of the user to be removed
	"""
	# Check permissions
	current_role, _ = get_user_role_hierarchy()
	allowed_roles = ["System Manager", "Sales Manager", "Regional Sales Head", "Branch Sales Head"]
	
	if current_role not in allowed_roles:
		frappe.only_for(["System Manager", "Sales Manager"])

	user_doc = frappe.get_doc("User", user)
	
	# All CRM roles that can be removed
	all_crm_roles = ["System Manager", "Sales Manager", "Regional Sales Head", 
	                  "Branch Sales Head", "Team Lead", "Sales User"]
	
	for role in all_crm_roles:
		user_doc.remove_roles(role)

	user_doc.save(ignore_permissions=True)
	frappe.msgprint(f"User {user} has been removed from CRM roles.")


def update_module_in_user(user, module):
	block_modules = frappe.get_all(
		"Module Def",
		fields=["name as module"],
		filters={"name": ["!=", module]},
	)

	if block_modules:
		user.set("block_modules", block_modules)


@frappe.whitelist()
def create_hierarchical_roles():
	"""
	Create the three hierarchical roles if they don't exist.
	Run with: bench --site [site] execute crm.api.user.create_hierarchical_roles
	"""
	roles_to_create = [
		{"role_name": "Regional Sales Head", "desk_access": 1, "is_custom": 0, "disabled": 0},
		{"role_name": "Branch Sales Head", "desk_access": 1, "is_custom": 0, "disabled": 0},
		{"role_name": "Team Lead", "desk_access": 1, "is_custom": 0, "disabled": 0}
	]
	
	created = []
	
	for role_data in roles_to_create:
		role_name = role_data.get("role_name")
		
		try:
			if frappe.db.exists("Role", role_name):
				print(f"✓ {role_name} already exists")
				created.append(role_name)
				continue
			
			role_doc = frappe.get_doc({"doctype": "Role", **role_data})
			role_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			print(f"✓ Created: {role_name}")
			created.append(role_name)
			
		except Exception as e:
			print(f"✗ Error creating {role_name}: {str(e)}")
	
	frappe.msgprint(f"Created {len(created)} roles!")
	return created
