# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Pull Request Management API
"""

import frappe
from typing import Dict, Any, List, Optional
from github_manager.github.api import get_github_api
from github_manager.github_manager.doctype.github_pull_request.github_pull_request import sync_pull_request


@frappe.whitelist()
def create_pull_request(
	repository: str,
	title: str,
	head: str,
	base: str,
	body: Optional[str] = None,
	draft: int = 0
) -> Dict[str, Any]:
	"""Create a new pull request.

	Args:
		repository: Repository full name (owner/repo)
		title: PR title
		head: Source branch
		base: Target branch
		body: PR description
		draft: Whether PR is a draft (1 or 0)

	Returns:
		Dictionary with PR data
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	pr_data = api.create_pull_request(
		owner=owner,
		repo=repo,
		title=title,
		head=head,
		base=base,
		body=body,
		draft=bool(int(draft))
	)

	# Sync to Frappe
	pr_number = pr_data.get("number")
	pr = sync_pull_request(repository, pr_number, pr_data)

	frappe.msgprint(f"Pull request #{pr_number} created successfully", indicator="green")

	return {
		"message": "Pull request created successfully",
		"pull_request": pr.name,
		"url": pr.url,
		"number": pr_number
	}


@frappe.whitelist()
def merge_pull_request(
	repository: str,
	pr_number: int,
	merge_method: str = "merge"
) -> Dict[str, Any]:
	"""Merge a pull request.

	Args:
		repository: Repository full name (owner/repo)
		pr_number: PR number
		merge_method: Merge method (merge, squash, rebase)

	Returns:
		Dictionary with merge result
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Validate merge method
	if merge_method not in ["merge", "squash", "rebase"]:
		frappe.throw("Invalid merge method. Use 'merge', 'squash', or 'rebase'")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	result = api.merge_pull_request(
		owner=owner,
		repo=repo,
		pull_number=pr_number,
		merge_method=merge_method
	)

	# Update PR in Frappe
	pr_name = f"PR-{repository}-{pr_number}"
	if frappe.db.exists("GitHub Pull Request", pr_name):
		# Fetch updated PR data
		updated_pr_data = api.get_pull_request(owner, repo, pr_number)
		sync_pull_request(repository, pr_number, updated_pr_data)

	frappe.msgprint(f"Pull request #{pr_number} merged successfully", indicator="green")

	return {
		"message": "Pull request merged successfully",
		"merged": result.get("merged", False),
		"sha": result.get("sha")
	}


@frappe.whitelist()
def close_pull_request(repository: str, pr_number: int) -> Dict[str, Any]:
	"""Close a pull request without merging.

	Args:
		repository: Repository full name (owner/repo)
		pr_number: PR number

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
	pr_data = api.close_pull_request(owner, repo, pr_number)

	# Update PR in Frappe
	pr_number_int = pr_data.get("number")
	sync_pull_request(repository, pr_number_int, pr_data)

	frappe.msgprint(f"Pull request #{pr_number} closed successfully", indicator="green")

	return {"message": "Pull request closed successfully"}


@frappe.whitelist()
def sync_pull_requests(repository: str, state: str = "open") -> Dict[str, Any]:
	"""Sync pull requests from GitHub.

	Args:
		repository: Repository full name (owner/repo)
		state: PR state (open, closed, all)

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
	prs = api.list_pull_requests(owner, repo, state=state)

	synced_count = 0
	for pr_data in prs:
		pr_number = pr_data.get("number")
		sync_pull_request(repository, pr_number, pr_data)
		synced_count += 1

	frappe.msgprint(f"Synced {synced_count} pull requests", indicator="green")

	return {
		"message": f"Synced {synced_count} pull requests",
		"count": synced_count
	}


@frappe.whitelist()
def get_pull_request_stats() -> Dict[str, Any]:
	"""Get pull request statistics for dashboard.

	Returns:
		Dictionary with PR stats
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	total_prs = frappe.db.count("GitHub Pull Request")
	open_prs = frappe.db.count("GitHub Pull Request", {"state": "open"})
	merged_prs = frappe.db.count("GitHub Pull Request", {"state": "merged"})
	closed_prs = frappe.db.count("GitHub Pull Request", {"state": "closed"})

	# Get recent PRs
	recent_prs = frappe.db.get_list(
		"GitHub Pull Request",
		fields=["name", "title", "repository", "state", "author", "created_at"],
		order_by="created_at desc",
		limit=10
	)

	# Get PR activity by repository
	pr_by_repo = frappe.db.sql("""
		SELECT repository, COUNT(*) as count
		FROM `tabGitHub Pull Request`
		GROUP BY repository
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)

	return {
		"total_prs": total_prs,
		"open_prs": open_prs,
		"merged_prs": merged_prs,
		"closed_prs": closed_prs,
		"recent_prs": recent_prs,
		"pr_by_repo": pr_by_repo
	}
