# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Dict, Any, List


class GitHubIssue(Document):
	"""GitHub Issue DocType for managing GitHub issues."""

	def sync_from_github(self, issue_data: Dict[str, Any]) -> None:
		"""Sync issue data from GitHub API response.

		Args:
			issue_data: GitHub issue data from API
		"""
		self.issue_id = str(issue_data.get("id"))
		self.issue_number = issue_data.get("number")
		self.title = issue_data.get("title")
		self.body = issue_data.get("body")
		self.url = issue_data.get("html_url")
		self.state = issue_data.get("state", "open")

		# Labels
		labels = issue_data.get("labels", [])
		if labels:
			label_names = [label.get("name") for label in labels if isinstance(label, dict)]
			self.labels = ", ".join(label_names)

		# Assignees
		assignees = issue_data.get("assignees", [])
		if assignees:
			assignee_names = [assignee.get("login") for assignee in assignees if isinstance(assignee, dict)]
			self.assignees = ", ".join(assignee_names)

		# Author
		author = issue_data.get("user", {})
		self.author = author.get("login")

		# Dates
		created_at = issue_data.get("created_at")
		if created_at:
			self.created_at = frappe.utils.get_datetime(created_at)

		updated_at = issue_data.get("updated_at")
		if updated_at:
			self.updated_at = frappe.utils.get_datetime(updated_at)

		closed_at = issue_data.get("closed_at")
		if closed_at:
			self.closed_at = frappe.utils.get_datetime(closed_at)

		# Closed by
		if issue_data.get("closed_by"):
			self.closed_by = issue_data["closed_by"].get("login")

		# Statistics
		self.comments = issue_data.get("comments", 0)

		self.is_synced = 1
		self.last_synced = frappe.utils.now()
		self.save()

	def get_github_data(self) -> Dict[str, Any]:
		"""Get issue data for GitHub API calls.

		Returns:
			Dictionary containing issue data
		"""
		data = {
			"title": self.title,
			"body": self.body
		}

		# Add labels if present
		if self.labels:
			data["labels"] = [label.strip() for label in self.labels.split(",")]

		# Add assignees if present
		if self.assignees:
			data["assignees"] = [assignee.strip() for assignee in self.assignees.split(",")]

		return data


def sync_issue(repository: str, issue_number: int, issue_data: Dict[str, Any]) -> "GitHubIssue":
	"""Sync or create a GitHub Issue from API data.

	Args:
		repository: Repository full name
		issue_number: Issue number
		issue_data: GitHub API response data

	Returns:
		GitHubIssue document
	"""
	name = f"ISSUE-{repository}-{issue_number}"

	if frappe.db.exists("GitHub Issue", name):
		issue = frappe.get_doc("GitHub Issue", name)
		issue.sync_from_github(issue_data)
	else:
		issue = frappe.get_doc({
			"doctype": "GitHub Issue",
			"repository": repository,
			"issue_number": issue_number
		})
		issue.insert(ignore_permissions=True)
		issue.sync_from_github(issue_data)

	return issue
