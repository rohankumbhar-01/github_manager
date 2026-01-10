# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from typing import Dict, Any, Optional


class GitHubAuditLog(Document):
	"""GitHub Audit Log DocType for tracking all GitHub actions."""
	pass


def create_audit_log(
	action_type: str,
	resource_type: str,
	resource_name: Optional[str] = None,
	request_payload: Optional[Dict[str, Any]] = None,
	response_data: Optional[Dict[str, Any]] = None,
	status: str = "success",
	error_message: Optional[str] = None
) -> "GitHubAuditLog":
	"""Create an audit log entry for GitHub actions.

	Args:
		action_type: Type of action (create, read, update, delete, merge, sync, list)
		resource_type: Type of resource (repository, pull_request, branch, release, issue, organization)
		resource_name: Name of the resource
		request_payload: Request data sent to GitHub
		response_data: Response data from GitHub
		status: Status of the action (success, failed, pending)
		error_message: Error message if action failed

	Returns:
		GitHubAuditLog document
	"""
	log = frappe.get_doc({
		"doctype": "GitHub Audit Log",
		"action_type": action_type,
		"resource_type": resource_type,
		"resource_name": resource_name,
		"user": frappe.session.user,
		"status": status,
		"request_payload": json.dumps(request_payload, indent=2) if request_payload else None,
		"response_data": json.dumps(response_data, indent=2) if response_data else None,
		"error_message": error_message,
		"ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None
	})

	log.insert(ignore_permissions=True)
	return log
