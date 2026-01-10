# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
GitHub API Service Layer with JWT Authentication and Rate Limiting
"""

import frappe
import requests
import jwt
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from github_manager.github_manager.doctype.github_audit_log.github_audit_log import create_audit_log


class GitHubAPIError(Exception):
	"""Custom exception for GitHub API errors."""
	pass


class GitHubRateLimitError(Exception):
	"""Custom exception for GitHub API rate limit errors."""
	pass


def handle_github_errors(func):
	"""Decorator to handle GitHub API errors and create audit logs."""
	@wraps(func)
	def wrapper(*args, **kwargs):
		try:
			result = func(*args, **kwargs)
			return result
		except GitHubRateLimitError as e:
			frappe.throw(str(e), title="GitHub Rate Limit Exceeded")
		except GitHubAPIError as e:
			frappe.throw(str(e), title="GitHub API Error")
		except Exception as e:
			frappe.log_error(f"GitHub API Error: {str(e)}", "GitHub API")
			frappe.throw(f"Unexpected error: {str(e)}", title="GitHub API Error")
	return wrapper


class GitHubAPI:
	"""GitHub API Client with App authentication."""

	def __init__(self):
		"""Initialize GitHub API client."""
		self.settings = self._get_settings()
		self.base_url = "https://api.github.com"
		self.access_token = None
		self.token_expires_at = None

	def _get_settings(self):
		"""Get active GitHub App Settings."""
		from github_manager.github_manager.doctype.github_app_settings.github_app_settings import get_github_settings
		settings = get_github_settings()
		if not settings:
			frappe.throw("No active GitHub App Settings found. Please configure GitHub App Settings first.")
		return settings

	def _generate_jwt(self) -> str:
		"""Generate JWT token for GitHub App authentication.

		Returns:
			JWT token string
		"""
		now = int(time.time())
		payload = {
			"iat": now - 60,  # Issued at time (60 seconds in the past to account for clock skew)
			"exp": now + (10 * 60),  # Expiration time (10 minutes from now)
			"iss": self.settings.app_id  # GitHub App's identifier
		}

		# Get private key
		private_key = self.settings.get_password("private_key")
		if not private_key:
			frappe.throw("Private key not found in GitHub App Settings")

		# Generate JWT
		token = jwt.encode(payload, private_key, algorithm="RS256")
		return token

	def _get_access_token(self) -> str:
		"""Get or refresh installation access token.

		Returns:
			Access token string
		"""
		# Check if we have a valid cached token
		if self.access_token and self.token_expires_at:
			if datetime.now() < self.token_expires_at - timedelta(minutes=5):
				return self.access_token

		# Generate new JWT
		jwt_token = self._generate_jwt()

		# Request installation access token
		url = f"{self.base_url}/app/installations/{self.settings.installation_id}/access_tokens"
		headers = {
			"Authorization": f"Bearer {jwt_token}",
			"Accept": "application/vnd.github+json",
			"X-GitHub-Api-Version": "2022-11-28"
		}

		response = requests.post(url, headers=headers)

		if response.status_code != 201:
			frappe.log_error(f"Failed to get access token: {response.text}", "GitHub API")
			raise GitHubAPIError(f"Failed to get access token: {response.status_code}")

		data = response.json()
		self.access_token = data.get("token")
		expires_at_str = data.get("expires_at")

		if expires_at_str:
			self.token_expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

		# Update settings
		self.settings.update_token_refresh()

		return self.access_token

	def _check_rate_limit(self, response: requests.Response) -> None:
		"""Check and update rate limit from response headers.

		Args:
			response: Response object from GitHub API
		"""
		remaining = response.headers.get("X-RateLimit-Remaining")
		reset = response.headers.get("X-RateLimit-Reset")

		if remaining and reset:
			remaining = int(remaining)
			reset_time = datetime.fromtimestamp(int(reset))

			# Update settings
			self.settings.update_rate_limit(remaining, reset_time.strftime("%Y-%m-%d %H:%M:%S"))

			# Warn if rate limit is low
			if remaining < 100:
				frappe.msgprint(
					f"GitHub API rate limit is low: {remaining} requests remaining. "
					f"Resets at {reset_time.strftime('%Y-%m-%d %H:%M:%S')}",
					indicator="orange"
				)

			# Raise error if rate limit exceeded
			if remaining == 0:
				raise GitHubRateLimitError(
					f"GitHub API rate limit exceeded. Resets at {reset_time.strftime('%Y-%m-%d %H:%M:%S')}"
				)

	def _make_request(
		self,
		method: str,
		endpoint: str,
		data: Optional[Dict[str, Any]] = None,
		params: Optional[Dict[str, Any]] = None,
		retry_count: int = 3
	) -> Dict[str, Any]:
		"""Make HTTP request to GitHub API with retry logic.

		Args:
			method: HTTP method (GET, POST, PUT, DELETE, PATCH)
			endpoint: API endpoint (without base URL)
			data: Request body data
			params: URL parameters
			retry_count: Number of retries on failure

		Returns:
			Response data as dictionary
		"""
		token = self._get_access_token()
		url = f"{self.base_url}/{endpoint.lstrip('/')}"

		headers = {
			"Authorization": f"Bearer {token}",
			"Accept": "application/vnd.github+json",
			"X-GitHub-Api-Version": "2022-11-28",
			"Content-Type": "application/json"
		}

		for attempt in range(retry_count):
			try:
				response = requests.request(
					method=method,
					url=url,
					headers=headers,
					json=data,
					params=params,
					timeout=30
				)

				# Check rate limit
				self._check_rate_limit(response)

				# Handle different status codes
				if response.status_code in [200, 201, 204]:
					return response.json() if response.text else {}

				elif response.status_code == 404:
					raise GitHubAPIError(f"Resource not found: {endpoint}")

				elif response.status_code == 403:
					raise GitHubAPIError(f"Access forbidden: {response.json().get('message', 'Unknown error')}")

				elif response.status_code == 422:
					raise GitHubAPIError(f"Validation failed: {response.json().get('message', 'Unknown error')}")

				else:
					error_msg = response.json().get("message", "Unknown error")
					raise GitHubAPIError(f"GitHub API error ({response.status_code}): {error_msg}")

			except requests.exceptions.Timeout:
				if attempt == retry_count - 1:
					raise GitHubAPIError("Request timeout after multiple retries")
				time.sleep(2 ** attempt)  # Exponential backoff

			except requests.exceptions.ConnectionError:
				if attempt == retry_count - 1:
					raise GitHubAPIError("Connection error after multiple retries")
				time.sleep(2 ** attempt)

		raise GitHubAPIError("Max retries exceeded")

	# Repository Methods

	@handle_github_errors
	def create_repository(
		self,
		name: str,
		description: Optional[str] = None,
		private: bool = True,
		org: Optional[str] = None,
		auto_init: bool = True
	) -> Dict[str, Any]:
		"""Create a new repository.

		Args:
			name: Repository name
			description: Repository description
			private: Whether repository is private
			org: Organization name (if creating under org)
			auto_init: Initialize with README

		Returns:
			Repository data from GitHub
		"""
		data = {
			"name": name,
			"description": description,
			"private": private,
			"auto_init": auto_init
		}

		# Remove None values
		data = {k: v for k, v in data.items() if v is not None}

		# Determine endpoint
		if org:
			endpoint = f"orgs/{org}/repos"
		else:
			endpoint = "user/repos"

		result = self._make_request("POST", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="create",
			resource_type="repository",
			resource_name=result.get("full_name"),
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def delete_repository(self, owner: str, repo: str) -> None:
		"""Delete a repository.

		Args:
			owner: Repository owner
			repo: Repository name
		"""
		endpoint = f"repos/{owner}/{repo}"
		self._make_request("DELETE", endpoint)

		# Create audit log
		create_audit_log(
			action_type="delete",
			resource_type="repository",
			resource_name=f"{owner}/{repo}",
			status="success"
		)

	@handle_github_errors
	def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
		"""Get repository details.

		Args:
			owner: Repository owner
			repo: Repository name

		Returns:
			Repository data from GitHub
		"""
		endpoint = f"repos/{owner}/{repo}"
		result = self._make_request("GET", endpoint)
		return result

	@handle_github_errors
	def list_repositories(self, org: Optional[str] = None, per_page: int = 30, page: int = 1) -> List[Dict[str, Any]]:
		"""List repositories.

		Args:
			org: Organization name (if listing org repos)
			per_page: Results per page
			page: Page number

		Returns:
			List of repository data from GitHub
		"""
		params = {"per_page": per_page, "page": page}

		if org:
			endpoint = f"orgs/{org}/repos"
		else:
			endpoint = "user/repos"

		result = self._make_request("GET", endpoint, params=params)
		return result if isinstance(result, list) else []

	# Pull Request Methods

	@handle_github_errors
	def create_pull_request(
		self,
		owner: str,
		repo: str,
		title: str,
		head: str,
		base: str,
		body: Optional[str] = None,
		draft: bool = False
	) -> Dict[str, Any]:
		"""Create a pull request.

		Args:
			owner: Repository owner
			repo: Repository name
			title: PR title
			head: Source branch
			base: Target branch
			body: PR description
			draft: Whether PR is a draft

		Returns:
			Pull request data from GitHub
		"""
		data = {
			"title": title,
			"head": head,
			"base": base,
			"body": body,
			"draft": draft
		}

		endpoint = f"repos/{owner}/{repo}/pulls"
		result = self._make_request("POST", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="create",
			resource_type="pull_request",
			resource_name=f"{owner}/{repo}#{result.get('number')}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def merge_pull_request(
		self,
		owner: str,
		repo: str,
		pull_number: int,
		merge_method: str = "merge"
	) -> Dict[str, Any]:
		"""Merge a pull request.

		Args:
			owner: Repository owner
			repo: Repository name
			pull_number: PR number
			merge_method: Merge method (merge, squash, rebase)

		Returns:
			Merge result from GitHub
		"""
		data = {"merge_method": merge_method}
		endpoint = f"repos/{owner}/{repo}/pulls/{pull_number}/merge"
		result = self._make_request("PUT", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="merge",
			resource_type="pull_request",
			resource_name=f"{owner}/{repo}#{pull_number}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def close_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
		"""Close a pull request.

		Args:
			owner: Repository owner
			repo: Repository name
			pull_number: PR number

		Returns:
			Updated PR data from GitHub
		"""
		data = {"state": "closed"}
		endpoint = f"repos/{owner}/{repo}/pulls/{pull_number}"
		result = self._make_request("PATCH", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="update",
			resource_type="pull_request",
			resource_name=f"{owner}/{repo}#{pull_number}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def list_pull_requests(
		self,
		owner: str,
		repo: str,
		state: str = "open",
		per_page: int = 30,
		page: int = 1
	) -> List[Dict[str, Any]]:
		"""List pull requests.

		Args:
			owner: Repository owner
			repo: Repository name
			state: PR state (open, closed, all)
			per_page: Results per page
			page: Page number

		Returns:
			List of PR data from GitHub
		"""
		params = {"state": state, "per_page": per_page, "page": page}
		endpoint = f"repos/{owner}/{repo}/pulls"
		result = self._make_request("GET", endpoint, params=params)
		return result if isinstance(result, list) else []

	@handle_github_errors
	def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
		"""Get pull request details.

		Args:
			owner: Repository owner
			repo: Repository name
			pull_number: PR number

		Returns:
			PR data from GitHub
		"""
		endpoint = f"repos/{owner}/{repo}/pulls/{pull_number}"
		return self._make_request("GET", endpoint)

	# Branch Methods

	@handle_github_errors
	def list_branches(self, owner: str, repo: str, per_page: int = 30, page: int = 1) -> List[Dict[str, Any]]:
		"""List branches.

		Args:
			owner: Repository owner
			repo: Repository name
			per_page: Results per page
			page: Page number

		Returns:
			List of branch data from GitHub
		"""
		params = {"per_page": per_page, "page": page}
		endpoint = f"repos/{owner}/{repo}/branches"
		result = self._make_request("GET", endpoint, params=params)
		return result if isinstance(result, list) else []

	@handle_github_errors
	def create_branch(self, owner: str, repo: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
		"""Create a new branch.

		Args:
			owner: Repository owner
			repo: Repository name
			branch_name: New branch name
			from_branch: Source branch

		Returns:
			Reference data from GitHub
		"""
		# Get SHA of the source branch
		source_ref = self._make_request("GET", f"repos/{owner}/{repo}/git/refs/heads/{from_branch}")
		sha = source_ref["object"]["sha"]

		# Create new branch
		data = {
			"ref": f"refs/heads/{branch_name}",
			"sha": sha
		}

		endpoint = f"repos/{owner}/{repo}/git/refs"
		result = self._make_request("POST", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="create",
			resource_type="branch",
			resource_name=f"{owner}/{repo}:{branch_name}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def delete_branch(self, owner: str, repo: str, branch_name: str) -> None:
		"""Delete a branch.

		Args:
			owner: Repository owner
			repo: Repository name
			branch_name: Branch name to delete
		"""
		endpoint = f"repos/{owner}/{repo}/git/refs/heads/{branch_name}"
		self._make_request("DELETE", endpoint)

		# Create audit log
		create_audit_log(
			action_type="delete",
			resource_type="branch",
			resource_name=f"{owner}/{repo}:{branch_name}",
			status="success"
		)

	# Release Methods

	@handle_github_errors
	def create_release(
		self,
		owner: str,
		repo: str,
		tag_name: str,
		name: Optional[str] = None,
		body: Optional[str] = None,
		draft: bool = False,
		prerelease: bool = False,
		target_commitish: Optional[str] = None
	) -> Dict[str, Any]:
		"""Create a release.

		Args:
			owner: Repository owner
			repo: Repository name
			tag_name: Tag name
			name: Release name
			body: Release notes
			draft: Whether release is a draft
			prerelease: Whether release is a pre-release
			target_commitish: Target branch/commit

		Returns:
			Release data from GitHub
		"""
		data = {
			"tag_name": tag_name,
			"name": name or tag_name,
			"body": body,
			"draft": draft,
			"prerelease": prerelease,
			"target_commitish": target_commitish
		}

		# Remove None values
		data = {k: v for k, v in data.items() if v is not None}

		endpoint = f"repos/{owner}/{repo}/releases"
		result = self._make_request("POST", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="create",
			resource_type="release",
			resource_name=f"{owner}/{repo}:{tag_name}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def delete_release(self, owner: str, repo: str, release_id: str) -> None:
		"""Delete a release.

		Args:
			owner: Repository owner
			repo: Repository name
			release_id: Release ID
		"""
		endpoint = f"repos/{owner}/{repo}/releases/{release_id}"
		self._make_request("DELETE", endpoint)

		# Create audit log
		create_audit_log(
			action_type="delete",
			resource_type="release",
			resource_name=f"{owner}/{repo}:{release_id}",
			status="success"
		)

	@handle_github_errors
	def list_releases(self, owner: str, repo: str, per_page: int = 30, page: int = 1) -> List[Dict[str, Any]]:
		"""List releases.

		Args:
			owner: Repository owner
			repo: Repository name
			per_page: Results per page
			page: Page number

		Returns:
			List of release data from GitHub
		"""
		params = {"per_page": per_page, "page": page}
		endpoint = f"repos/{owner}/{repo}/releases"
		result = self._make_request("GET", endpoint, params=params)
		return result if isinstance(result, list) else []

	# Issue Methods

	@handle_github_errors
	def create_issue(
		self,
		owner: str,
		repo: str,
		title: str,
		body: Optional[str] = None,
		labels: Optional[List[str]] = None,
		assignees: Optional[List[str]] = None
	) -> Dict[str, Any]:
		"""Create an issue.

		Args:
			owner: Repository owner
			repo: Repository name
			title: Issue title
			body: Issue description
			labels: List of label names
			assignees: List of assignee usernames

		Returns:
			Issue data from GitHub
		"""
		data = {
			"title": title,
			"body": body,
			"labels": labels or [],
			"assignees": assignees or []
		}

		endpoint = f"repos/{owner}/{repo}/issues"
		result = self._make_request("POST", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="create",
			resource_type="issue",
			resource_name=f"{owner}/{repo}#{result.get('number')}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def close_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
		"""Close an issue.

		Args:
			owner: Repository owner
			repo: Repository name
			issue_number: Issue number

		Returns:
			Updated issue data from GitHub
		"""
		data = {"state": "closed"}
		endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
		result = self._make_request("PATCH", endpoint, data=data)

		# Create audit log
		create_audit_log(
			action_type="update",
			resource_type="issue",
			resource_name=f"{owner}/{repo}#{issue_number}",
			request_payload=data,
			response_data=result,
			status="success"
		)

		return result

	@handle_github_errors
	def list_issues(
		self,
		owner: str,
		repo: str,
		state: str = "open",
		per_page: int = 30,
		page: int = 1
	) -> List[Dict[str, Any]]:
		"""List issues.

		Args:
			owner: Repository owner
			repo: Repository name
			state: Issue state (open, closed, all)
			per_page: Results per page
			page: Page number

		Returns:
			List of issue data from GitHub
		"""
		params = {"state": state, "per_page": per_page, "page": page}
		endpoint = f"repos/{owner}/{repo}/issues"
		result = self._make_request("GET", endpoint, params=params)
		return result if isinstance(result, list) else []

	# Organization Methods

	@handle_github_errors
	def get_organization(self, org: str) -> Dict[str, Any]:
		"""Get organization details.

		Args:
			org: Organization name

		Returns:
			Organization data from GitHub
		"""
		endpoint = f"orgs/{org}"
		return self._make_request("GET", endpoint)


def get_github_api() -> GitHubAPI:
	"""Get GitHub API client instance.

	Returns:
		GitHubAPI instance
	"""
	return GitHubAPI()
