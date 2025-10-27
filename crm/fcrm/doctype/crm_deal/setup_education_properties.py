"""Setup education customizations - Run with bench console"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

frappe.init()
frappe.connect()

print("Applying education customizations...")

# 1. CRM ORGANIZATION → INSTITUTE
print("\n1. Updating Organization fields...")
org_fields = {
    "organization_name": "Institute Name",
    "website": "Institute Website",
    "annual_revenue": "Annual Budget",
    "no_of_employees": "No. of Students",
    "industry": "Education Type"
}

for fieldname, label in org_fields.items():
    make_property_setter(
        doc_type="CRM Organization",
        field_name=fieldname,
        property="label",
        value=label,
        property_type="Data"
    )
    print(f"  ✓ {fieldname} → {label}")

# Update student count options
make_property_setter(
    doc_type="CRM Organization",
    field_name="no_of_employees",
    property="options",
    value="1-50\n51-200\n201-500\n501-1000\n1000+",
    property_type="Text"
)

# 2. CRM DEAL - Rename Products Tab
print("\n2. Updating Deal fields...")
make_property_setter(
    doc_type="CRM Deal",
    field_name="products_tab",
    property="label",
    value="Courses & Programs",
    property_type="Data"
)

deal_fields = {
    "organization": "Institute",
    "annual_revenue": "Budget"
}

for fieldname, label in deal_fields.items():
    make_property_setter(
        doc_type="CRM Deal",
        field_name=fieldname,
        property="label",
        value=label,
        property_type="Data"
    )
    print(f"  ✓ {fieldname} → {label}")

# 3. CRM PRODUCTS → COURSES
print("\n3. Updating Product fields...")
course_fields = {
    "product_code": "Course",
    "product_name": "Course Name",
    "rate": "Course Fee",
    "qty": "Duration (Months)",
    "discount_percentage": "Scholarship %",
    "discount_amount": "Scholarship Amount",
    "amount": "Total Fee",
    "net_amount": "Net Fee After Scholarship"
}

for fieldname, label in course_fields.items():
    make_property_setter(
        doc_type="CRM Products",
        field_name=fieldname,
        property="label",
        value=label,
        property_type="Data"
    )
    print(f"  ✓ {fieldname} → {label}")

# 4. CREATE EDUCATION INDUSTRIES
print("\n4. Creating education industries...")
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
            print(f"  ✓ Created: {industry_name}")
        except Exception as e:
            print(f"  ⚠ Error creating {industry_name}: {e}")

frappe.db.commit()
frappe.clear_cache()

print("\n✓ Education customizations applied successfully!")
print("\nPlease clear cache: bench --site pumo.localhost clear-cache")

