# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Branch Management API
"""

import frappe
from typing import Dict, Any, List
from github_manager.github.api import get_github_api


@frappe.whitelist()
def list_branches(repository: str) -> Dict[str, Any]:
	"""List all branches in a repository.

	Args:
		repository: Repository full name (owner/repo)

	Returns:
		Dictionary with list of branches
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer", "GitHub Viewer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	branches = api.list_branches(owner, repo)

	return {
		"message": f"Found {len(branches)} branches",
		"branches": branches
	}


@frappe.whitelist()
def create_branch(
	repository: str,
	branch_name: str,
	from_branch: str = "main"
) -> Dict[str, Any]:
	"""Create a new branch.

	Args:
		repository: Repository full name (owner/repo)
		branch_name: New branch name
		from_branch: Source branch to create from

	Returns:
		Dictionary with branch data
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	api = get_github_api()
	result = api.create_branch(owner, repo, branch_name, from_branch)

	frappe.msgprint(f"Branch '{branch_name}' created successfully", indicator="green")

	return {
		"message": "Branch created successfully",
		"branch": branch_name,
		"ref": result.get("ref")
	}


@frappe.whitelist()
def delete_branch(repository: str, branch_name: str) -> Dict[str, Any]:
	"""Delete a branch.

	Args:
		repository: Repository full name (owner/repo)
		branch_name: Branch name to delete

	Returns:
		Dictionary with result
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Parse owner and repo
	parts = repository.split("/")
	if len(parts) != 2:
		frappe.throw("Invalid repository format. Use 'owner/repo'")

	owner, repo = parts

	# Check if it's the default branch
	repo_doc = frappe.get_doc("GitHub Repository", repository)
	if repo_doc and branch_name == repo_doc.default_branch:
		frappe.throw(f"Cannot delete default branch '{branch_name}'")

	api = get_github_api()
	api.delete_branch(owner, repo, branch_name)

	frappe.msgprint(f"Branch '{branch_name}' deleted successfully", indicator="green")

	return {"message": "Branch deleted successfully"}
