# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def create_event_with_participants(event_data):
	"""
	Create an event with automatic contact creation for email-only participants
	"""
	try:
		# Parse the event data
		if isinstance(event_data, str):
			import json
			event_data = json.loads(event_data)
		
		# Process event participants
		participants = event_data.get('event_participants', [])
		processed_participants = []
		
		for participant in participants:
			processed_participant = {
				'email': participant.get('email')
			}
			
			# If we have reference fields, use them
			if participant.get('reference_doctype') and participant.get('reference_docname'):
				processed_participant['reference_doctype'] = participant['reference_doctype']
				processed_participant['reference_docname'] = participant['reference_docname']
			else:
				# Create a contact for email-only participants
				email = participant.get('email')
				if email and '@' in email:
					contact_name = create_or_get_contact_for_email(email)
					processed_participant['reference_doctype'] = 'Contact'
					processed_participant['reference_docname'] = contact_name
			
			processed_participants.append(processed_participant)
		
		# Update the event data with processed participants
		event_data['event_participants'] = processed_participants
		
		# Create the event
		event = frappe.get_doc(event_data)
		event.insert()
		
		return {
			'status': 'success',
			'name': event.name,
			'message': _('Event created successfully')
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating event: {str(e)}")
		return {
			'status': 'error',
			'message': str(e)
		}


@frappe.whitelist()
def get_events_by_reference(doctype, docname):
	"""
	Get events linked to a specific doctype/docname
	This bypasses the field validation restriction on reference_doctype
	"""
	try:
		if not doctype or not docname:
			return []
		
		events = frappe.db.sql("""
			SELECT 
				name,
				status,
				subject,
				description,
				starts_on,
				ends_on,
				all_day,
				event_type,
				color,
				owner,
				reference_doctype,
				reference_docname,
				creation
			FROM `tabEvent`
			WHERE reference_doctype = %s 
				AND reference_docname = %s
				AND status = 'Open'
			ORDER BY creation DESC
		""", (doctype, docname), as_dict=True)
		
		return events
	except Exception as e:
		frappe.log_error(f"Error fetching events by reference: {str(e)}")
		return []


def create_or_get_contact_for_email(email):
	"""
	Create a contact for the given email or return existing one
	"""
	# Check if contact already exists with this email
	existing_contact = frappe.db.get_value('Contact', {'email_id': email}, 'name')
	if existing_contact:
		return existing_contact
	
	# Create new contact
	contact = frappe.get_doc({
		'doctype': 'Contact',
		'first_name': email.split('@')[0],
		'email_id': email
	})
	contact.insert(ignore_permissions=True)
	return contact.name
