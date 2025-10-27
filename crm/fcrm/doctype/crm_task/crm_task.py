# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign, remove as unassign
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


class CRMTask(Document):
	def after_insert(self):
		self.assign_to()

	def validate(self):
		if self.is_new() or not self.assigned_to:
			return

		if self.get_doc_before_save().assigned_to != self.assigned_to:
			self.unassign_from_previous_user(self.get_doc_before_save().assigned_to)
			self.assign_to()
		
		# Check if task is overdue and update status in real-time
		self.check_and_update_overdue_status()
	
	def before_save(self):
		pass

	def unassign_from_previous_user(self, user):
		unassign(self.doctype, self.name, user)

	def assign_to(self):
		if self.assigned_to:
			assign({
				"assign_to": [self.assigned_to],
				"doctype": self.doctype,
				"name": self.name,
				"description": self.title or self.description,
			})

	def check_and_update_overdue_status(self):
		"""Check if current task is overdue and update status in real-time"""
		try:
			from frappe.utils import now_datetime
			
			# Only check if task has a due date
			if not self.due_date:
				return
				
			# Check if current time is past due date (time is negative)
			if now_datetime() > self.due_date:
				# Force status to Overdue if not already Done or Canceled
				if self.status not in ["Done", "Canceled"]:
					self.status = "Overdue"
		except Exception as e:
			# If there's any error, just skip the overdue check
			# This prevents the 500 error
			pass

	def get_time_to_due(self):
		"""Calculate time to due and return with styling info"""
		from frappe.utils import now_datetime, time_diff_in_seconds
		
		if not self.due_date:
			return {"value": "", "is_overdue": False, "color": ""}
		
		now = now_datetime()
		due = self.due_date
		
		# Calculate time difference in seconds
		diff_seconds = time_diff_in_seconds(due, now)
		
		# Check if overdue (negative time)
		is_overdue = diff_seconds < 0
		
		# Format time display
		if is_overdue:
			# Show as overdue (negative)
			hours = abs(diff_seconds) // 3600
			minutes = (abs(diff_seconds) % 3600) // 60
			if hours > 0:
				value = f"-{hours}h {minutes}m overdue"
			else:
				value = f"-{minutes}m overdue"
			color = "red"
		else:
			# Show as remaining time
			hours = diff_seconds // 3600
			minutes = (diff_seconds % 3600) // 60
			if hours > 0:
				value = f"{hours}h {minutes}m left"
			else:
				value = f"{minutes}m left"
			color = "green" if diff_seconds > 3600 else "orange"  # Green if >1hr, orange if <1hr
		
		return {
			"value": value,
			"is_overdue": is_overdue,
			"color": color
		}


	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Title',
				'type': 'Data',
				'key': 'title',
				'width': '16rem',
			},
			{
				'label': 'Status',
				'type': 'Select',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Priority',
				'type': 'Select',
				'key': 'priority',
				'width': '8rem',
			},
			{
				'label': 'Time to Due',
				'type': 'Datetime',
				'key': 'time_to_due',
				'width': '10rem',
			},
			{
				'label': 'Due Date',
				'type': 'Date',
				'key': 'due_date',
				'width': '8rem',
			},
			{
				'label': 'Assigned To',
				'type': 'Link',
				'key': 'assigned_to',
				'width': '10rem',
			},
			{
				'label': 'Last Modified',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]

		rows = [
			"name",
			"title",
			"description",
			"assigned_to",
			"time_to_due",
			"due_date",
			"status",
			"priority",
			"reference_doctype",
			"reference_docname",
			"modified",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "title",
			"kanban_fields": '["description", "priority", "creation"]'
		}

# Simple and clean - no scheduled jobs needed!

@frappe.whitelist()
def get_time_to_due_info(task_name):
	"""Get time to due information with styling for a specific task"""
	try:
		task = frappe.get_doc("CRM Task", task_name)
		return task.get_time_to_due()
	except Exception as e:
		return {"value": "Error", "is_overdue": False, "color": "gray"}
