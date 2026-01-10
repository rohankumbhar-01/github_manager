# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Dict, Any


class GitHubPullRequest(Document):
	"""GitHub Pull Request DocType for managing GitHub pull requests."""

	def sync_from_github(self, pr_data: Dict[str, Any]) -> None:
		"""Sync pull request data from GitHub API response.

		Args:
			pr_data: GitHub pull request data from API
		"""
		self.pr_id = str(pr_data.get("id"))
		self.pr_number = pr_data.get("number")
		self.title = pr_data.get("title")
		self.body = pr_data.get("body")
		self.url = pr_data.get("html_url")
		self.state = pr_data.get("state", "open")

		# Handle merged state
		if pr_data.get("merged"):
			self.state = "merged"
			self.merged = 1
			merged_at = pr_data.get("merged_at")
			if merged_at:
				self.merged_at = frappe.utils.get_datetime(merged_at)
			merger = pr_data.get("merged_by")
			if merger:
				self.merged_by = merger.get("login")

		# Branches
		head = pr_data.get("head", {})
		base = pr_data.get("base", {})
		self.head_branch = head.get("ref")
		self.base_branch = base.get("ref")

		# Author
		author = pr_data.get("user", {})
		self.author = author.get("login")

		# Dates
		created_at = pr_data.get("created_at")
		if created_at:
			self.created_at = frappe.utils.get_datetime(created_at)

		updated_at = pr_data.get("updated_at")
		if updated_at:
			self.updated_at = frappe.utils.get_datetime(updated_at)

		# Statistics
		self.comments = pr_data.get("comments", 0)
		self.commits = pr_data.get("commits", 0)
		self.additions = pr_data.get("additions", 0)
		self.deletions = pr_data.get("deletions", 0)

		# Mergeable state
		self.mergeable = pr_data.get("mergeable", False)
		self.mergeable_state = pr_data.get("mergeable_state")
		self.draft = pr_data.get("draft", False)

		self.is_synced = 1
		self.last_synced = frappe.utils.now()
		self.save()

	def get_github_data(self) -> Dict[str, Any]:
		"""Get pull request data for GitHub API calls.

		Returns:
			Dictionary containing PR data
		"""
		return {
			"title": self.title,
			"body": self.body,
			"head": self.head_branch,
			"base": self.base_branch,
			"draft": self.draft
		}


def sync_pull_request(repository: str, pr_number: int, pr_data: Dict[str, Any]) -> "GitHubPullRequest":
	"""Sync or create a GitHub Pull Request from API data.

	Args:
		repository: Repository full name
		pr_number: Pull request number
		pr_data: GitHub API response data

	Returns:
		GitHubPullRequest document
	"""
	name = f"PR-{repository}-{pr_number}"

	if frappe.db.exists("GitHub Pull Request", name):
		pr = frappe.get_doc("GitHub Pull Request", name)
		pr.sync_from_github(pr_data)
	else:
		pr = frappe.get_doc({
			"doctype": "GitHub Pull Request",
			"repository": repository,
			"pr_number": pr_number
		})
		pr.insert(ignore_permissions=True)
		pr.sync_from_github(pr_data)

	return pr
