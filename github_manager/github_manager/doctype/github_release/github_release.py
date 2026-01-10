# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Dict, Any


class GitHubRelease(Document):
	"""GitHub Release DocType for managing GitHub releases."""

	def sync_from_github(self, release_data: Dict[str, Any]) -> None:
		"""Sync release data from GitHub API response.

		Args:
			release_data: GitHub release data from API
		"""
		self.release_id = str(release_data.get("id"))
		self.tag_name = release_data.get("tag_name")
		self.name_title = release_data.get("name") or self.tag_name
		self.body = release_data.get("body")
		self.url = release_data.get("html_url")
		self.target_commitish = release_data.get("target_commitish")
		self.draft = release_data.get("draft", False)
		self.prerelease = release_data.get("prerelease", False)

		# Author
		author = release_data.get("author", {})
		self.author = author.get("login")

		# Dates
		created_at = release_data.get("created_at")
		if created_at:
			self.created_at = frappe.utils.get_datetime(created_at)

		published_at = release_data.get("published_at")
		if published_at:
			self.published_at = frappe.utils.get_datetime(published_at)

		self.is_synced = 1
		self.last_synced = frappe.utils.now()
		self.save()

	def get_github_data(self) -> Dict[str, Any]:
		"""Get release data for GitHub API calls.

		Returns:
			Dictionary containing release data
		"""
		return {
			"tag_name": self.tag_name,
			"name": self.name_title,
			"body": self.body,
			"target_commitish": self.target_commitish or "main",
			"draft": self.draft,
			"prerelease": self.prerelease
		}


def sync_release(repository: str, tag_name: str, release_data: Dict[str, Any]) -> "GitHubRelease":
	"""Sync or create a GitHub Release from API data.

	Args:
		repository: Repository full name
		tag_name: Release tag name
		release_data: GitHub API response data

	Returns:
		GitHubRelease document
	"""
	name = f"REL-{repository}-{tag_name}"

	if frappe.db.exists("GitHub Release", name):
		release = frappe.get_doc("GitHub Release", name)
		release.sync_from_github(release_data)
	else:
		release = frappe.get_doc({
			"doctype": "GitHub Release",
			"repository": repository,
			"tag_name": tag_name
		})
		release.insert(ignore_permissions=True)
		release.sync_from_github(release_data)

	return release
