# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Release Management API
"""

import frappe
from typing import Dict, Any, Optional
from github_manager.github.api import get_github_api
from github_manager.github_manager.doctype.github_release.github_release import sync_release


@frappe.whitelist()
def create_release(
	repository: str,
	tag_name: str,
	name: Optional[str] = None,
	body: Optional[str] = None,
	draft: int = 0,
	prerelease: int = 0,
	target_commitish: Optional[str] = None
) -> Dict[str, Any]:
	"""Create a new release.

	Args:
		repository: Repository full name (owner/repo)
		tag_name: Tag name
		name: Release name
		body: Release notes
		draft: Whether release is a draft (1 or 0)
		prerelease: Whether release is a pre-release (1 or 0)
		target_commitish: Target branch/commit

	Returns:
		Dictionary with release data
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	release_data = api.create_release(
		owner=owner,
		repo=repo,
		tag_name=tag_name,
		name=name,
		body=body,
		draft=bool(int(draft)),
		prerelease=bool(int(prerelease)),
		target_commitish=target_commitish
	)

	# Sync to Frappe
	release = sync_release(repository, tag_name, release_data)

	frappe.msgprint(f"Release '{tag_name}' created successfully", indicator="green")

	return {
		"message": "Release created successfully",
		"release": release.name,
		"url": release.url,
		"tag_name": tag_name
	}


@frappe.whitelist()
def delete_release(repository: str, release_id: str) -> Dict[str, Any]:
	"""Delete a release.

	Args:
		repository: Repository full name (owner/repo)
		release_id: Release ID from GitHub

	Returns:
		Dictionary with result
	"""
	frappe.only_for("GitHub Admin")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	api.delete_release(owner, repo, release_id)

	frappe.msgprint(f"Release deleted successfully", indicator="green")

	return {"message": "Release deleted successfully"}


@frappe.whitelist()
def sync_releases(repository: str) -> Dict[str, Any]:
	"""Sync releases from GitHub.

	Args:
		repository: Repository full name (owner/repo)

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
	releases = api.list_releases(owner, repo)

	synced_count = 0
	for release_data in releases:
		tag_name = release_data.get("tag_name")
		sync_release(repository, tag_name, release_data)
		synced_count += 1

	frappe.msgprint(f"Synced {synced_count} releases", indicator="green")

	return {
		"message": f"Synced {synced_count} releases",
		"count": synced_count
	}


@frappe.whitelist()
def get_release_stats() -> Dict[str, Any]:
	"""Get release statistics for dashboard.

	Returns:
		Dictionary with release stats
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	total_releases = frappe.db.count("GitHub Release")
	draft_releases = frappe.db.count("GitHub Release", {"draft": 1})
	prereleases = frappe.db.count("GitHub Release", {"prerelease": 1})

	# Get recent releases
	recent_releases = frappe.db.get_list(
		"GitHub Release",
		fields=["name", "name_title", "tag_name", "repository", "published_at"],
		filters={"draft": 0},
		order_by="published_at desc",
		limit=10
	)

	# Get releases by repository
	releases_by_repo = frappe.db.sql("""
		SELECT repository, COUNT(*) as count
		FROM `tabGitHub Release`
		GROUP BY repository
		ORDER BY count DESC
		LIMIT 5
	""", as_dict=True)

	return {
		"total_releases": total_releases,
		"draft_releases": draft_releases,
		"prereleases": prereleases,
		"recent_releases": recent_releases,
		"releases_by_repo": releases_by_repo
	}
