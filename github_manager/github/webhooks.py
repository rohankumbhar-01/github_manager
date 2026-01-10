# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

"""
GitHub Webhook Handlers
"""

import frappe
import hmac
import hashlib
import json
from typing import Dict, Any
from github_manager.github_manager.doctype.github_repository.github_repository import sync_repository
from github_manager.github_manager.doctype.github_pull_request.github_pull_request import sync_pull_request
from github_manager.github_manager.doctype.github_release.github_release import sync_release
from github_manager.github_manager.doctype.github_issue.github_issue import sync_issue
from github_manager.github_manager.doctype.github_app_settings.github_app_settings import get_github_settings


def verify_signature(payload: bytes, signature: str) -> bool:
	"""Verify GitHub webhook signature.

	Args:
		payload: Request payload
		signature: GitHub signature from header

	Returns:
		True if signature is valid, False otherwise
	"""
	settings = get_github_settings()
	if not settings or not settings.webhook_secret:
		frappe.log_error("Webhook secret not configured", "GitHub Webhook")
		return False

	webhook_secret = settings.get_password("webhook_secret")
	if not webhook_secret:
		return False

	# Compute HMAC
	expected_signature = "sha256=" + hmac.new(
		webhook_secret.encode(),
		payload,
		hashlib.sha256
	).hexdigest()

	# Compare signatures
	return hmac.compare_digest(expected_signature, signature)


@frappe.whitelist(allow_guest=True)
def handle_webhook() -> Dict[str, Any]:
	"""Handle incoming GitHub webhooks.

	Returns:
		Dictionary with status
	"""
	try:
		# Get headers
		signature = frappe.request.headers.get("X-Hub-Signature-256")
		event = frappe.request.headers.get("X-GitHub-Event")

		# Get payload
		payload = frappe.request.get_data()

		# Verify signature
		if not verify_signature(payload, signature):
			frappe.local.response.http_status_code = 401
			return {"status": "error", "message": "Invalid signature"}

		# Parse payload
		data = json.loads(payload)

		# Handle different events
		if event == "push":
			handle_push_event(data)
		elif event == "pull_request":
			handle_pull_request_event(data)
		elif event == "release":
			handle_release_event(data)
		elif event == "issues":
			handle_issue_event(data)
		elif event == "repository":
			handle_repository_event(data)
		else:
			frappe.logger().info(f"Unhandled webhook event: {event}")

		return {"status": "success"}

	except Exception as e:
		frappe.log_error(f"Webhook error: {str(e)}", "GitHub Webhook")
		frappe.local.response.http_status_code = 500
		return {"status": "error", "message": str(e)}


def handle_push_event(data: Dict[str, Any]) -> None:
	"""Handle push event.

	Args:
		data: Webhook payload data
	"""
	repository = data.get("repository", {})
	full_name = repository.get("full_name")

	frappe.logger().info(f"Push event for repository: {full_name}")

	# You can add custom logic here (e.g., trigger CI/CD)


def handle_pull_request_event(data: Dict[str, Any]) -> None:
	"""Handle pull request event.

	Args:
		data: Webhook payload data
	"""
	action = data.get("action")
	pr_data = data.get("pull_request", {})
	repository = data.get("repository", {})
	full_name = repository.get("full_name")
	pr_number = pr_data.get("number")

	frappe.logger().info(f"Pull request {action} event for {full_name}#{pr_number}")

	# Sync PR to Frappe
	if action in ["opened", "closed", "reopened", "synchronize", "edited"]:
		frappe.enqueue(
			sync_pull_request,
			queue="short",
			repository=full_name,
			pr_number=pr_number,
			pr_data=pr_data
		)


def handle_release_event(data: Dict[str, Any]) -> None:
	"""Handle release event.

	Args:
		data: Webhook payload data
	"""
	action = data.get("action")
	release_data = data.get("release", {})
	repository = data.get("repository", {})
	full_name = repository.get("full_name")
	tag_name = release_data.get("tag_name")

	frappe.logger().info(f"Release {action} event for {full_name}:{tag_name}")

	# Sync release to Frappe
	if action in ["published", "created", "edited"]:
		frappe.enqueue(
			sync_release,
			queue="short",
			repository=full_name,
			tag_name=tag_name,
			release_data=release_data
		)
	elif action == "deleted":
		# Delete release from Frappe
		release_name = f"REL-{full_name}-{tag_name}"
		if frappe.db.exists("GitHub Release", release_name):
			frappe.delete_doc("GitHub Release", release_name, force=1)


def handle_issue_event(data: Dict[str, Any]) -> None:
	"""Handle issue event.

	Args:
		data: Webhook payload data
	"""
	action = data.get("action")
	issue_data = data.get("issue", {})
	repository = data.get("repository", {})
	full_name = repository.get("full_name")
	issue_number = issue_data.get("number")

	# Skip if this is a pull request
	if "pull_request" in issue_data:
		return

	frappe.logger().info(f"Issue {action} event for {full_name}#{issue_number}")

	# Sync issue to Frappe
	if action in ["opened", "closed", "reopened", "edited"]:
		frappe.enqueue(
			sync_issue,
			queue="short",
			repository=full_name,
			issue_number=issue_number,
			issue_data=issue_data
		)


def handle_repository_event(data: Dict[str, Any]) -> None:
	"""Handle repository event.

	Args:
		data: Webhook payload data
	"""
	action = data.get("action")
	repository = data.get("repository", {})
	full_name = repository.get("full_name")

	frappe.logger().info(f"Repository {action} event for {full_name}")

	# Sync repository to Frappe
	if action in ["created", "edited"]:
		frappe.enqueue(
			sync_repository,
			queue="short",
			full_name=full_name,
			repo_data=repository
		)
	elif action == "deleted":
		# Delete repository from Frappe
		if frappe.db.exists("GitHub Repository", full_name):
			frappe.delete_doc("GitHub Repository", full_name, force=1)
