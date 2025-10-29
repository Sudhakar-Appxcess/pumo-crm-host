# Copyright (c) 2025, AppXcess
# Education Center Customization Script

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def apply_education_customizations():
    """Apply all education-specific customizations"""
    frappe.clear_cache()
    print("Starting education customizations...")
    
    # ============================================
    # 1. CRM ORGANIZATION → INSTITUTE
    # ============================================
    
    # Update Organization doctype label to Institute
    set_property_if_not_exists(
        doc_type="CRM Organization",
        property="label",
        value="Institute",
        property_type="Data"
    )
    
    # Update Organization fields to education context
    org_field_updates = {
        "organization_name": "Institute Name",
        "website": "Institute Website",
        "annual_revenue": "Annual Budget",
        "no_of_employees": "No. of Students",
        "industry": "Education Type"
    }
    
    for fieldname, label in org_field_updates.items():
        set_property_if_not_exists(
            doc_type="CRM Organization",
            field_name=fieldname,
            property="label",
            value=label,
            property_type="Data"
        )
    
    # Update student count options
    set_property_if_not_exists(
        doc_type="CRM Organization",
        field_name="no_of_employees",
        property="options",
        value="1-50\n51-200\n201-500\n501-1000\n1000+",
        property_type="Text"
    )
    
    # ============================================
    # 2. CRM DEAL - HIDE PRODUCTS TAB
    # ============================================
    
    # Hide Products tab (or rename to Courses)
    set_property_if_not_exists(
        doc_type="CRM Deal",
        field_name="products_tab",
        property="hidden",
        value=0,  # Set to 1 to hide, 0 to show
        property_type="Check"
    )
    
    # Rename products tab to "Courses & Programs"
    set_property_if_not_exists(
        doc_type="CRM Deal",
        field_name="products_tab",
        property="label",
        value="Courses & Programs",
        property_type="Data"
    )
    
    # Update deal field labels
    deal_field_updates = {
        "organization": "Institute",
        "annual_revenue": "Budget",
        "expected_deal_value": "Expected Course Fee",
        "deal_value": "Total Course Fee",
        "expected_closure_date": "Expected Admission Date",
        "closed_date": "Admission Date"
    }
    
    for fieldname, label in deal_field_updates.items():
        set_property_if_not_exists(
            doc_type="CRM Deal",
            field_name=fieldname,
            property="label",
            value=label,
            property_type="Data"
        )
    
    # ============================================
    # 3. CRM PRODUCTS → COURSES
    # ============================================
    
    course_field_updates = {
        "product_code": "Course",
        "product_name": "Course Name",
        "rate": "Course Fee",
        "qty": "Duration (Months)",
        "discount_percentage": "Scholarship %",
        "discount_amount": "Scholarship Amount",
        "amount": "Total Fee",
        "net_amount": "Net Fee After Scholarship"
    }
    
    for fieldname, label in course_field_updates.items():
        set_property_if_not_exists(
            doc_type="CRM Products",
            field_name=fieldname,
            property="label",
            value=label,
            property_type="Data"
        )
    
    # ============================================
    # 4. CREATE EDUCATION INDUSTRIES
    # ============================================
    
    industries = [
        "K-12 Education",
        "Higher Education",
        "Professional Training",
        "Skill Development",
        "Vocational Training",
        "Coaching Center",
        "Language Institute",
        "Online Education",
        "Distance Learning"
    ]
    
    for industry_name in industries:
        if not frappe.db.exists("CRM Industry", industry_name):
            try:
                industry_doc = frappe.new_doc("CRM Industry")
                industry_doc.industry_name = industry_name
                industry_doc.insert(ignore_permissions=True)
                print(f"Created industry: {industry_name}")
            except Exception as e:
                print(f"Error creating industry {industry_name}: {e}")
    
    print("Education customizations completed successfully!")
    frappe.clear_cache()
    
    return "Education customizations applied successfully!"


def set_property_if_not_exists(doc_type, property, value, property_type="Data", field_name=None):
    """Set property only if it doesn't already exist"""
    try:
        filters = {"doc_type": doc_type, "property": property}
        if field_name:
            filters["field_name"] = field_name
        
        if frappe.db.exists("Property Setter", filters):
            print(f"Property Setter already exists for {doc_type}.{field_name or ''}[{property}]")
            return
        
        make_property_setter(
            doc_type=doc_type,
            field_name=field_name,
            property=property,
            value=value,
            property_type=property_type
        )
        print(f"Created property setter: {doc_type}.{field_name or ''}[{property}] = {value}")
    except Exception as e:
        print(f"Error setting property for {doc_type}: {e}")


def revert_education_customizations():
    """Revert all education-specific customizations"""
    print("Reverting education customizations...")
    
    # Delete property setters
    property_setters = frappe.get_all(
        "Property Setter",
        filters={
            "doc_type": ["in", ["CRM Organization", "CRM Deal", "CRM Products"]]
        },
        fields=["name"]
    )
    
    for ps in property_setters:
        try:
            frappe.delete_doc("Property Setter", ps.name)
        except:
            pass
    
    frappe.clear_cache()
    print("Education customizations reverted!")
    return "Education customizations reverted successfully!"



