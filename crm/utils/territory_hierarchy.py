# Copyright (c) 2024, AppXcess and contributors
# For hierarchical territory-based user management

import frappe
from frappe import _


# Define the role hierarchy
ROLE_HIERARCHY = {
    "System Manager": {
        "can_manage_roles": ["System Manager", "Regional Sales Head", "Branch Sales Head", "Team Lead", "Sales User"],
        "has_territory_access": True,
        "min_territory_level": 0  # 0 = root/all territories
    },
    "Regional Sales Head": {
        "can_manage_roles": ["Regional Sales Head", "Branch Sales Head", "Team Lead", "Sales User"],
        "has_territory_access": True,
        "min_territory_level": 1  # 1 = Regional level
    },
    "Branch Sales Head": {
        "can_manage_roles": ["Branch Sales Head", "Team Lead", "Sales User"],
        "has_territory_access": True,
        "min_territory_level": 2  # 2 = Branch level
    },
    "Team Lead": {
        "can_manage_roles": ["Team Lead", "Sales User"],
        "has_territory_access": True,
        "min_territory_level": 3  # 3 = Team level
    },
    "Sales User": {
        "can_manage_roles": [],
        "has_territory_access": True,
        "min_territory_level": 4  # 4 = Individual level
    },
    # Backward compatibility - keep existing roles
    "Sales Manager": {
        "can_manage_roles": ["Sales Manager", "Sales User"],
        "has_territory_access": True,
        "min_territory_level": 1
    }
}


def get_user_role_hierarchy(user=None):
    """
    Get the primary role and its hierarchy for a user.
    Returns the highest level role the user has.
    """
    if not user:
        user = frappe.session.user
    
    roles = frappe.get_roles(user)
    
    # Check from highest to lowest authority
    for role in ["System Manager", "Regional Sales Head", "Branch Sales Head", "Team Lead", "Sales Manager", "Sales User"]:
        if role in roles:
            return role, ROLE_HIERARCHY.get(role, {})
    
    return None, {}


def can_user_manage_role(user_role, target_role):
    """
    Check if a user with user_role can manage a user with target_role.
    """
    if not user_role or not target_role:
        return False
    
    hierarchy = ROLE_HIERARCHY.get(user_role, {})
    manageable_roles = hierarchy.get("can_manage_roles", [])
    
    return target_role in manageable_roles


def get_user_territory_manager(user):
    """
    Get the territory where this user is assigned as manager.
    """
    territory = frappe.db.get_value(
        "CRM Territory",
        {"territory_manager": user},
        "name"
    )
    return territory


def get_user_assigned_territory(user):
    """
    Get the primary territory assigned to a user via User Permissions.
    Returns the most specific territory.
    """
    user_permissions = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "CRM Territory"},
        fields=["for_value"],
        order_by="name DESC"
    )
    
    if user_permissions:
        # Return the first (most recent) territory
        return user_permissions[0].for_value
    
    return None


def get_user_accessible_territories(user):
    """
    Get all territories a user can access based on their User Permissions.
    """
    user_permissions = frappe.get_user_permissions(user)
    territories = user_permissions.get("CRM Territory", [])
    
    if territories:
        return [t.get("doc") for t in territories]
    
    return []


def assign_territory_to_user(user, territory, hide_descendants=False):
    """
    Assign a territory permission to a user.
    This creates a User Permission record.
    
    Args:
        user: User email
        territory: Territory name
        hide_descendants: If True, user can only see this territory, not child territories
    """
    if not frappe.db.exists("CRM Territory", territory):
        frappe.throw(_("Territory {0} does not exist").format(territory))
    
    if not frappe.db.exists("User", user):
        frappe.throw(_("User {0} does not exist").format(user))
    
    # Check if permission already exists
    if frappe.db.exists(
        "User Permission",
        {
            "user": user,
            "allow": "CRM Territory",
            "for_value": territory
        }
    ):
        frappe.msgprint(_("User {0} already has permission for territory {1}").format(user, territory))
        return
    
    # Create permission
    permission_doc = frappe.get_doc({
        "doctype": "User Permission",
        "user": user,
        "allow": "CRM Territory",
        "for_value": territory,
        "apply_to_all_doctypes": 1,
        "hide_descendants": 1 if hide_descendants else 0
    })
    
    permission_doc.insert(ignore_permissions=True)
    return permission_doc


def remove_territory_from_user(user, territory):
    """
    Remove a territory permission from a user.
    """
    permissions = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "CRM Territory",
            "for_value": territory
        }
    )
    
    for perm in permissions:
        frappe.delete_doc("User Permission", perm.name, ignore_permissions=True, force=1)


def get_user_territory_scope(user):
    """
    Get the territory scope for a user.
    Returns dictionary with territory info and access level.
    """
    role, hierarchy = get_user_role_hierarchy(user)
    
    assigned_territory = get_user_assigned_territory(user)
    manageable_roles = hierarchy.get("can_manage_roles", [])
    
    return {
        "role": role,
        "assigned_territory": assigned_territory,
        "can_manage_roles": manageable_roles,
        "min_territory_level": hierarchy.get("min_territory_level", 4),
        "has_territory_restriction": bool(assigned_territory)
    }


def can_user_access_territory(user, territory):
    """
    Check if a user can access a specific territory.
    Uses User Permissions to determine access.
    """
    # If user has "System Manager" role, they have access to all territories
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Check User Permissions
    user_permissions = frappe.get_user_permissions(user)
    territories = user_permissions.get("CRM Territory", [])
    
    if not territories:
        # No territory restrictions
        return True
    
    # Check if territory is in allowed territories
    allowed_territories = [t.get("doc") for t in territories]
    
    if territory in allowed_territories:
        return True
    
    # Check if user has access to parent territory
    territory_doc = frappe.get_doc("CRM Territory", territory)
    parent = territory_doc.get("parent_crm_territory")
    
    if parent and parent in allowed_territories:
        # Check if descendants are hidden
        for perm in territories:
            if perm.get("doc") == parent:
                return not perm.get("hide_descendants", False)
    
    return False


@frappe.whitelist()
def get_management_info(user=None):
    """
    Get management information for the current user or specified user.
    """
    user = user or frappe.session.user
    return get_user_territory_scope(user)


@frappe.whitelist()
def assign_user_to_territory(user, territory, hide_descendants=False):
    """
    Assign a user to a territory.
    Only accessible by authorized roles.
    """
    current_user_role, _ = get_user_role_hierarchy()
    
    if not current_user_role or current_user_role == "Sales User":
        frappe.throw(_("Insufficient permissions to assign territory"))
    
    return assign_territory_to_user(user, territory, hide_descendants)
