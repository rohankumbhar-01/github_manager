# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Repository Management API
"""

import frappe
from typing import Dict, Any, List, Optional
from github_manager.github.api import get_github_api
from github_manager.github_manager.doctype.github_repository.github_repository import sync_repository


@frappe.whitelist()
def create_repository(
	name: str,
	description: Optional[str] = None,
	is_private: int = 1,
	organization: Optional[str] = None
) -> Dict[str, Any]:
	"""Create a new GitHub repository.

	Args:
		name: Repository name
		description: Repository description
		is_private: Whether repository is private (1 or 0)
		organization: Organization name (optional)

	Returns:
		Dictionary with repository data
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	api = get_github_api()
	repo_data = api.create_repository(
		name=name,
		description=description,
		private=bool(int(is_private)),
		org=organization,
		auto_init=True
	)

	# Sync to Frappe
	full_name = repo_data.get("full_name")
	repo = sync_repository(full_name, repo_data)

	frappe.msgprint(f"Repository {full_name} created successfully", indicator="green")

	return {
		"message": "Repository created successfully",
		"repository": repo.name,
		"url": repo.url
	}


@frappe.whitelist()
def delete_repository(repository: str) -> Dict[str, Any]:
	"""Delete a GitHub repository.

	Args:
		repository: Repository full name (owner/repo)

	Returns:
		Dictionary with success message
	"""
	frappe.only_for("GitHub Admin")

	# Confirm action
	if not frappe.db.exists("GitHub Repository", repository):
		frappe.throw(f"Repository {repository} not found in Frappe")

	repo_doc = frappe.get_doc("GitHub Repository", repository)

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	# Delete from GitHub
	api = get_github_api()
	api.delete_repository(owner, repo)

	# Delete from Frappe
	frappe.delete_doc("GitHub Repository", repository, force=1)

	frappe.msgprint(f"Repository {repository} deleted successfully", indicator="green")

	return {"message": "Repository deleted successfully"}


@frappe.whitelist()
def sync_repositories(organization: Optional[str] = None) -> Dict[str, Any]:
	"""Sync repositories from GitHub.

	Args:
		organization: Organization name (optional)

	Returns:
		Dictionary with sync results
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	api = get_github_api()
	repos = api.list_repositories(org=organization)

	synced_count = 0
	for repo_data in repos:
		full_name = repo_data.get("full_name")
		sync_repository(full_name, repo_data)
		synced_count += 1

	frappe.msgprint(f"Synced {synced_count} repositories", indicator="green")

	return {
		"message": f"Synced {synced_count} repositories",
		"count": synced_count
	}


@frappe.whitelist()
def get_repository_stats() -> Dict[str, Any]:
	"""Get repository statistics for dashboard.

	Returns:
		Dictionary with repository stats
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	total_repos = frappe.db.count("GitHub Repository")
	private_repos = frappe.db.count("GitHub Repository", {"is_private": 1})
	public_repos = total_repos - private_repos
	archived_repos = frappe.db.count("GitHub Repository", {"archived": 1})

	# Get top languages
	languages = frappe.db.sql("""
		SELECT language, COUNT(*) as count
		FROM `tabGitHub Repository`
		WHERE language IS NOT NULL AND language != ''
		GROUP BY language
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)

	# Get recent repos
	recent_repos = frappe.db.get_list(
		"GitHub Repository",
		fields=["name", "repository_name", "url", "stars", "language", "created_at"],
		order_by="created_at desc",
		limit=5
	)

	return {
		"total_repos": total_repos,
		"private_repos": private_repos,
		"public_repos": public_repos,
		"archived_repos": archived_repos,
		"top_languages": languages,
		"recent_repos": recent_repos
	}
