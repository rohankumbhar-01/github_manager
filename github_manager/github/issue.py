# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Issue Management API
"""

import frappe
from typing import Dict, Any, Optional, List
from github_manager.github.api import get_github_api
from github_manager.github_manager.doctype.github_issue.github_issue import sync_issue


@frappe.whitelist()
def create_issue(
	repository: str,
	title: str,
	body: Optional[str] = None,
	labels: Optional[str] = None,
	assignees: Optional[str] = None
) -> Dict[str, Any]:
	"""Create a new issue.

	Args:
		repository: Repository full name (owner/repo)
		title: Issue title
		body: Issue description
		labels: Comma-separated list of label names
		assignees: Comma-separated list of assignee usernames

	Returns:
		Dictionary with issue data
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	# Parse labels and assignees
	label_list = [l.strip() for l in labels.split(",")] if labels else []
	assignee_list = [a.strip() for a in assignees.split(",")] if assignees else []

	api = get_github_api()
	issue_data = api.create_issue(
		owner=owner,
		repo=repo,
		title=title,
		body=body,
		labels=label_list,
		assignees=assignee_list
	)

	# Sync to Frappe
	issue_number = issue_data.get("number")
	issue = sync_issue(repository, issue_number, issue_data)

	frappe.msgprint(f"Issue #{issue_number} created successfully", indicator="green")

	return {
		"message": "Issue created successfully",
		"issue": issue.name,
		"url": issue.url,
		"number": issue_number
	}


@frappe.whitelist()
def close_issue(repository: str, issue_number: int) -> Dict[str, Any]:
	"""Close an issue.

	Args:
		repository: Repository full name (owner/repo)
		issue_number: Issue number

	Returns:
		Dictionary with result
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	issue_data = api.close_issue(owner, repo, issue_number)

	# Update issue in Frappe
	sync_issue(repository, issue_number, issue_data)

	frappe.msgprint(f"Issue #{issue_number} closed successfully", indicator="green")

	return {"message": "Issue closed successfully"}


@frappe.whitelist()
def sync_issues(repository: str, state: str = "open") -> Dict[str, Any]:
	"""Sync issues from GitHub.

	Args:
		repository: Repository full name (owner/repo)
		state: Issue state (open, closed, all)

	Returns:
		Dictionary with sync results
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	issues = api.list_issues(owner, repo, state=state)

	synced_count = 0
	for issue_data in issues:
		# Skip pull requests (GitHub API returns PRs as issues)
		if "pull_request" not in issue_data:
			issue_number = issue_data.get("number")
			sync_issue(repository, issue_number, issue_data)
			synced_count += 1

	frappe.msgprint(f"Synced {synced_count} issues", indicator="green")

	return {
		"message": f"Synced {synced_count} issues",
		"count": synced_count
	}


@frappe.whitelist()
def get_issue_stats() -> Dict[str, Any]:
	"""Get issue statistics for dashboard.

	Returns:
		Dictionary with issue stats
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	total_issues = frappe.db.count("GitHub Issue")
	open_issues = frappe.db.count("GitHub Issue", {"state": "open"})
	closed_issues = frappe.db.count("GitHub Issue", {"state": "closed"})

	# Get recent issues
	recent_issues = frappe.db.get_list(
		"GitHub Issue",
		fields=["name", "title", "repository", "state", "author", "created_at"],
		order_by="created_at desc",
		limit=10
	)

	# Get issues by repository
	issues_by_repo = frappe.db.sql("""
		SELECT repository, COUNT(*) as count
		FROM `tabGitHub Issue`
		WHERE state = 'open'
		GROUP BY repository
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)

	return {
		"total_issues": total_issues,
		"open_issues": open_issues,
		"closed_issues": closed_issues,
		"recent_issues": recent_issues,
		"issues_by_repo": issues_by_repo
	}
