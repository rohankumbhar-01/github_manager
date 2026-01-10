# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Dict, Any, Optional


class GitHubRepository(Document):
	"""GitHub Repository DocType for managing GitHub repositories."""

	def before_save(self) -> None:
		"""Set computed fields before saving."""
		if self.repository_name:
			if self.organization:
				self.full_name = f"{self.organization}/{self.repository_name}"
				self.owner_type = "Organization"
			else:
				# Get authenticated user from GitHub settings
				self.full_name = self.repository_name
				self.owner_type = "User"

		if self.full_name and not self.url:
			self.url = f"https://github.com/{self.full_name}"

	def sync_from_github(self, repo_data: Dict[str, Any]) -> None:
		"""Sync repository data from GitHub API response.

		Args:
			repo_data: GitHub repository data from API
		"""
		self.repo_id = str(repo_data.get("id"))
		self.full_name = repo_data.get("full_name")
		self.description = repo_data.get("description")
		self.url = repo_data.get("html_url")
		self.clone_url = repo_data.get("clone_url")
		self.default_branch = repo_data.get("default_branch", "main")
		self.is_private = repo_data.get("private", False)
		self.visibility = "private" if self.is_private else "public"
		self.stars = repo_data.get("stargazers_count", 0)
		self.forks = repo_data.get("forks_count", 0)
		self.open_issues = repo_data.get("open_issues_count", 0)
		self.language = repo_data.get("language")
		self.size = repo_data.get("size", 0)
		self.archived = repo_data.get("archived", False)

		# Parse created_at
		created_at = repo_data.get("created_at")
		if created_at:
			self.created_at = frappe.utils.get_datetime(created_at)

		# Handle organization
		owner = repo_data.get("owner", {})
		if owner.get("type") == "Organization":
			org_name = owner.get("login")
			if org_name and frappe.db.exists("GitHub Organization", org_name):
				self.organization = org_name
				self.owner_type = "Organization"

		self.is_synced = 1
		self.last_synced = frappe.utils.now()
		self.save()

	def get_github_data(self) -> Dict[str, Any]:
		"""Get repository data for GitHub API calls.

		Returns:
			Dictionary containing repository data
		"""
		return {
			"name": self.repository_name,
			"description": self.description,
			"private": self.is_private,
			"auto_init": True,
			"default_branch": self.default_branch
		}


def sync_repository(full_name: str, repo_data: Dict[str, Any]) -> "GitHubRepository":
	"""Sync or create a GitHub Repository from API data.

	Args:
		full_name: Full repository name (owner/repo)
		repo_data: GitHub API response data

	Returns:
		GitHubRepository document
	"""
	if frappe.db.exists("GitHub Repository", full_name):
		repo = frappe.get_doc("GitHub Repository", full_name)
		repo.sync_from_github(repo_data)
	else:
		# Extract repo name from full_name
		repo_name = full_name.split("/")[-1]
		repo = frappe.get_doc({
			"doctype": "GitHub Repository",
			"repository_name": repo_name
		})
		repo.insert(ignore_permissions=True)
		repo.sync_from_github(repo_data)

	return repo
