# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	"""Get context for GitHub Dashboard page."""
	context.no_cache = 1

	# Check permissions
	if not frappe.has_permission("GitHub Repository", "read"):
		frappe.throw("You don't have permission to access GitHub Manager", frappe.PermissionError)

	context.title = "GitHub Manager"
