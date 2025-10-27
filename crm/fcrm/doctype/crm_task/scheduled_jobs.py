# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def update_overdue_tasks():
	"""Scheduled job to update tasks to Overdue status if they are past due date"""
	from crm.fcrm.doctype.crm_task.crm_task import CRMTask
	
	try:
		updated_count = CRMTask.update_overdue_tasks()
		if updated_count > 0:
			frappe.logger().info(f"Updated {updated_count} tasks to Overdue status")
	except Exception as e:
		frappe.logger().error(f"Error updating overdue tasks: {str(e)}")


@frappe.whitelist()
def manual_update_overdue_tasks():
	"""Manual API endpoint to update overdue tasks"""
	return update_overdue_tasks()
