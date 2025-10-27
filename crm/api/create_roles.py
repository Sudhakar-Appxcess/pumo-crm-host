"""
Create hierarchical roles for territory management
Run with: bench --site [site] execute crm.api.create_roles.create_roles
"""

import frappe


def create_roles():
    """Create the three new hierarchical roles."""
    
    roles_to_create = [
        {
            "role_name": "Regional Sales Head",
            "desk_access": 1,
            "is_custom": 0,
            "disabled": 0
        },
        {
            "role_name": "Branch Sales Head",
            "desk_access": 1,
            "is_custom": 0,
            "disabled": 0
        },
        {
            "role_name": "Team Lead",
            "desk_access": 1,
            "is_custom": 0,
            "disabled": 0
        }
    ]
    
    created = []
    
    print("\n=== Creating Hierarchical Roles ===\n")
    
    for role_data in roles_to_create:
        role_name = role_data.get("role_name")
        
        try:
            # Check if role already exists
            if frappe.db.exists("Role", role_name):
                print(f"✓ {role_name} - Already exists")
                created.append(role_name)
                continue
            
            # Create the role
            role_doc = frappe.get_doc({
                "doctype": "Role",
                **role_data
            })
            role_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            
            print(f"✓ {role_name} - Created successfully")
            created.append(role_name)
            
        except Exception as e:
            print(f"✗ {role_name} - Error: {str(e)}")
            frappe.log_error(f"Error creating role {role_name}: {str(e)}")
    
    print(f"\n=== Complete ===")
    print(f"Created {len(created)} out of {len(roles_to_create)} roles")
    
    if created:
        print("\nNew roles:")
        for role in created:
            print(f"  - {role}")
    
    print("\nYou can now:")
    print("1. Go to Settings → Roles to see the new roles")
    print("2. Assign these roles to users")
    print("3. Set up User Permissions for territory access")
    
    return created

