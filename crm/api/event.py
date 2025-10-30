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
		
		# Ensure reference_doctype and reference_docname are set on the Event
		# If not provided, try to get from first participant
		if not event_data.get('reference_doctype') or not event_data.get('reference_docname'):
			participants = event_data.get('event_participants', [])
			if participants and len(participants) > 0:
				first_participant = participants[0]
				if first_participant.get('reference_doctype') and first_participant.get('reference_docname'):
					event_data['reference_doctype'] = first_participant['reference_doctype']
					event_data['reference_docname'] = first_participant['reference_docname']
		
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
def update_event_with_participants(name, event_data):
	"""
	Update an event with automatic contact creation for email-only participants
	"""
	try:
		# Parse the event data
		if isinstance(event_data, str):
			import json
			event_data = json.loads(event_data)
		
		# Get existing event
		event = frappe.get_doc('Event', name)
		
		# Update basic fields
		if 'subject' in event_data:
			event.subject = event_data['subject']
		if 'description' in event_data:
			event.description = event_data.get('description', '')
		if 'starts_on' in event_data:
			event.starts_on = event_data['starts_on']
		if 'ends_on' in event_data:
			event.ends_on = event_data['ends_on']
		if 'all_day' in event_data:
			event.all_day = event_data['all_day']
		if 'event_type' in event_data:
			event.event_type = event_data['event_type']
		if 'color' in event_data:
			event.color = event_data['color']
		
		# Update reference fields if provided
		if 'reference_doctype' in event_data and event_data.get('reference_doctype'):
			event.reference_doctype = event_data['reference_doctype']
		if 'reference_docname' in event_data and event_data.get('reference_docname'):
			event.reference_docname = event_data['reference_docname']
		
		# Process event participants if provided
		if 'event_participants' in event_data:
			participants = event_data['event_participants']
			processed_participants = []
			
			# Clear existing participants
			event.event_participants = []
			
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
			
			# Add processed participants
			for participant in processed_participants:
				event.append('event_participants', participant)
		
		event.save()
		
		return {
			'status': 'success',
			'name': event.name,
			'message': _('Event updated successfully')
		}
		
	except Exception as e:
		frappe.log_error(f"Error updating event: {str(e)}")
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
