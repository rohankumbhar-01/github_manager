# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Dict, Any


class GitHubOrganization(Document):
	"""GitHub Organization DocType for managing GitHub organizations."""

	def before_save(self) -> None:
		"""Set URL before saving."""
		if self.org_name and not self.url:
			self.url = f"https://github.com/{self.org_name}"

	def sync_from_github(self, org_data: Dict[str, Any]) -> None:
		"""Sync organization data from GitHub API response.

		Args:
			org_data: GitHub organization data from API
		"""
		self.org_id = str(org_data.get("id"))
		self.description = org_data.get("description")
		self.avatar_url = org_data.get("avatar_url")
		self.url = org_data.get("html_url")
		self.is_synced = 1
		self.last_synced = frappe.utils.now()
		self.save()


def sync_organization(org_name: str, org_data: Dict[str, Any]) -> "GitHubOrganization":
	"""Sync or create a GitHub Organization from API data.

	Args:
		org_name: Organization name
		org_data: GitHub API response data

	Returns:
		GitHubOrganization document
	"""
	if frappe.db.exists("GitHub Organization", org_name):
		org = frappe.get_doc("GitHub Organization", org_name)
		org.sync_from_github(org_data)
	else:
		org = frappe.get_doc({
			"doctype": "GitHub Organization",
			"org_name": org_name
		})
		org.insert(ignore_permissions=True)
		org.sync_from_github(org_data)

	return org
