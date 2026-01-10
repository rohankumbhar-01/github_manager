# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Called after app installation."""
	create_custom_roles()
	create_workspace()
	frappe.db.commit()


def create_custom_roles():
	"""Create custom roles for GitHub Manager."""
	roles = [
		{
			"role_name": "GitHub Admin",
			"desk_access": 1,
		},
		{
			"role_name": "GitHub Maintainer",
			"desk_access": 1,
		},
		{
			"role_name": "GitHub Viewer",
			"desk_access": 1,
		}
	]

	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.get_doc({
				"doctype": "Role",
				**role_data
			})
			role.insert(ignore_permissions=True)
			frappe.logger().info(f"Created role: {role_data['role_name']}")


def create_workspace():
	"""Create GitHub Manager Workspace."""
	if frappe.db.exists("Workspace", "GitHub Manager"):
		return

	workspace = frappe.get_doc({
		"doctype": "Workspace",
		"title": "GitHub Manager",
		"icon": "github",
		"module": "GitHub Manager",
		"public": 1,
		"links": [
			{
				"label": "Dashboard",
				"type": "Link",
				"link_to": "/app/github",
				"link_type": "Link"
			},
			{
				"label": "Repositories",
				"type": "Link",
				"link_to": "GitHub Repository",
				"link_type": "DocType"
			},
			{
				"label": "Pull Requests",
				"type": "Link",
				"link_to": "GitHub Pull Request",
				"link_type": "DocType"
			},
			{
				"label": "Issues",
				"type": "Link",
				"link_to": "GitHub Issue",
				"link_type": "DocType"
			},
			{
				"label": "Releases",
				"type": "Link",
				"link_to": "GitHub Release",
				"link_type": "DocType"
			},
			{
				"label": "Settings",
				"type": "Link",
				"link_to": "GitHub App Settings",
				"link_type": "DocType"
			},
			{
				"label": "Audit Log",
				"type": "Link",
				"link_to": "GitHub Audit Log",
				"link_type": "DocType"
			}
		]
	})

	try:
		workspace.insert(ignore_permissions=True)
		frappe.logger().info("Created GitHub Manager workspace")
	except Exception as e:
		frappe.log_error(f"Failed to create workspace: {str(e)}", "GitHub Manager Install")
