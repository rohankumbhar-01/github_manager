# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
Background Jobs for syncing GitHub data
"""

import frappe
from typing import Optional
from github_manager.github.api import get_github_api
from github_manager.github_manager.doctype.github_repository.github_repository import sync_repository
from github_manager.github_manager.doctype.github_pull_request.github_pull_request import sync_pull_request
from github_manager.github_manager.doctype.github_release.github_release import sync_release
from github_manager.github_manager.doctype.github_issue.github_issue import sync_issue


def sync_all_repositories(organization: Optional[str] = None) -> None:
	"""Background job to sync all repositories from GitHub.

	Args:
		organization: Organization name (optional)
	"""
	try:
		api = get_github_api()

		page = 1
		per_page = 100
		total_synced = 0

		while True:
			repos = api.list_repositories(org=organization, per_page=per_page, page=page)

			if not repos:
				break

			for repo_data in repos:
				try:
					full_name = repo_data.get("full_name")
					sync_repository(full_name, repo_data)
					total_synced += 1
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Failed to sync repository {repo_data.get('full_name')}: {str(e)}", "GitHub Sync")
					continue

			# Check if there are more pages
			if len(repos) < per_page:
				break

			page += 1

		frappe.logger().info(f"Synced {total_synced} repositories from GitHub")

	except Exception as e:
		frappe.log_error(f"Failed to sync repositories: {str(e)}", "GitHub Sync")
		raise


def sync_repository_pull_requests(repository: str, state: str = "all") -> None:
	"""Background job to sync pull requests for a repository.

	Args:
		repository: Repository full name (owner/repo)
		state: PR state (open, closed, all)
	"""
	try:
		parts = repository.split("/")
		if len(parts) != 2:
			frappe.throw("Invalid repository format. Use 'owner/repo'")

		owner, repo = parts
		api = get_github_api()

		page = 1
		per_page = 100
		total_synced = 0

		while True:
			prs = api.list_pull_requests(owner, repo, state=state, per_page=per_page, page=page)

			if not prs:
				break

			for pr_data in prs:
				try:
					pr_number = pr_data.get("number")
					sync_pull_request(repository, pr_number, pr_data)
					total_synced += 1
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Failed to sync PR #{pr_data.get('number')}: {str(e)}", "GitHub Sync")
					continue

			# Check if there are more pages
			if len(prs) < per_page:
				break

			page += 1

		frappe.logger().info(f"Synced {total_synced} pull requests for {repository}")

	except Exception as e:
		frappe.log_error(f"Failed to sync pull requests for {repository}: {str(e)}", "GitHub Sync")
		raise


def sync_repository_releases(repository: str) -> None:
	"""Background job to sync releases for a repository.

	Args:
		repository: Repository full name (owner/repo)
	"""
	try:
		parts = repository.split("/")
		if len(parts) != 2:
			frappe.throw("Invalid repository format. Use 'owner/repo'")

		owner, repo = parts
		api = get_github_api()

		page = 1
		per_page = 100
		total_synced = 0

		while True:
			releases = api.list_releases(owner, repo, per_page=per_page, page=page)

			if not releases:
				break

			for release_data in releases:
				try:
					tag_name = release_data.get("tag_name")
					sync_release(repository, tag_name, release_data)
					total_synced += 1
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Failed to sync release {release_data.get('tag_name')}: {str(e)}", "GitHub Sync")
					continue

			# Check if there are more pages
			if len(releases) < per_page:
				break

			page += 1

		frappe.logger().info(f"Synced {total_synced} releases for {repository}")

	except Exception as e:
		frappe.log_error(f"Failed to sync releases for {repository}: {str(e)}", "GitHub Sync")
		raise


def sync_repository_issues(repository: str, state: str = "all") -> None:
	"""Background job to sync issues for a repository.

	Args:
		repository: Repository full name (owner/repo)
		state: Issue state (open, closed, all)
	"""
	try:
		parts = repository.split("/")
		if len(parts) != 2:
			frappe.throw("Invalid repository format. Use 'owner/repo'")

		owner, repo = parts
		api = get_github_api()

		page = 1
		per_page = 100
		total_synced = 0

		while True:
			issues = api.list_issues(owner, repo, state=state, per_page=per_page, page=page)

			if not issues:
				break

			for issue_data in issues:
				# Skip pull requests (GitHub API returns PRs as issues)
				if "pull_request" in issue_data:
					continue

				try:
					issue_number = issue_data.get("number")
					sync_issue(repository, issue_number, issue_data)
					total_synced += 1
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Failed to sync issue #{issue_data.get('number')}: {str(e)}", "GitHub Sync")
					continue

			# Check if there are more pages
			if len(issues) < per_page:
				break

			page += 1

		frappe.logger().info(f"Synced {total_synced} issues for {repository}")

	except Exception as e:
		frappe.log_error(f"Failed to sync issues for {repository}: {str(e)}", "GitHub Sync")
		raise


@frappe.whitelist()
def enqueue_sync_all_repositories(organization: Optional[str] = None) -> None:
	"""Enqueue background job to sync all repositories.

	Args:
		organization: Organization name (optional)
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	frappe.enqueue(
		sync_all_repositories,
		queue="long",
		timeout=3600,
		organization=organization,
		job_name=f"github_sync_repositories_{organization or 'user'}"
	)

	frappe.msgprint("Repository sync has been queued. This may take a few minutes.", indicator="blue")


@frappe.whitelist()
def enqueue_sync_repository_data(repository: str) -> None:
	"""Enqueue background jobs to sync all data for a repository.

	Args:
		repository: Repository full name (owner/repo)
	"""
	frappe.only_for("GitHub Admin", "GitHub Maintainer")

	# Enqueue PRs sync
	frappe.enqueue(
		sync_repository_pull_requests,
		queue="long",
		timeout=1800,
		repository=repository,
		state="all",
		job_name=f"github_sync_prs_{repository.replace('/', '_')}"
	)

	# Enqueue releases sync
	frappe.enqueue(
		sync_repository_releases,
		queue="long",
		timeout=1800,
		repository=repository,
		job_name=f"github_sync_releases_{repository.replace('/', '_')}"
	)

	# Enqueue issues sync
	frappe.enqueue(
		sync_repository_issues,
		queue="long",
		timeout=1800,
		repository=repository,
		state="all",
		job_name=f"github_sync_issues_{repository.replace('/', '_')}"
	)

	frappe.msgprint(
		f"Sync jobs for {repository} have been queued. This may take a few minutes.",
		indicator="blue"
	)


def scheduled_sync_open_prs() -> None:
	"""Scheduled job to sync open PRs for all repositories (runs hourly)."""
	repositories = frappe.get_all("GitHub Repository", pluck="name")

	for repo in repositories:
		try:
			frappe.enqueue(
				sync_repository_pull_requests,
				queue="long",
				timeout=1800,
				repository=repo,
				state="open",
				job_name=f"scheduled_sync_prs_{repo.replace('/', '_')}"
			)
		except Exception as e:
			frappe.log_error(f"Failed to enqueue PR sync for {repo}: {str(e)}", "GitHub Scheduled Sync")


def scheduled_sync_repositories() -> None:
	"""Scheduled job to sync all repositories (runs daily)."""
	try:
		frappe.enqueue(
			sync_all_repositories,
			queue="long",
			timeout=3600,
			job_name="scheduled_sync_all_repositories"
		)
	except Exception as e:
		frappe.log_error(f"Failed to enqueue repository sync: {str(e)}", "GitHub Scheduled Sync")
