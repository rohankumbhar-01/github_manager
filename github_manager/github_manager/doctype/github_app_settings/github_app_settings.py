# Copyright (c) 2026, Dexciss Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from typing import Optional


class GitHubAppSettings(Document):
	"""GitHub App Settings DocType for managing GitHub App authentication."""

	def validate(self) -> None:
		"""Validate the GitHub App Settings."""
		self.validate_private_key_format()

	def validate_private_key_format(self) -> None:
		"""Validate that the private key is in PEM format."""
		if self.private_key:
			private_key = self.get_password("private_key")
			if not private_key or not private_key.strip().startswith("-----BEGIN"):
				frappe.throw("Private Key must be in PEM format (starting with -----BEGIN)")

	def update_rate_limit(self, remaining: int, reset_at: str) -> None:
		"""Update rate limit information from GitHub API response.

		Args:
			remaining: Remaining API calls
			reset_at: Reset timestamp
		"""
		self.db_set("rate_limit_remaining", remaining, update_modified=False)
		self.db_set("rate_limit_reset_at", reset_at, update_modified=False)

	def update_token_refresh(self) -> None:
		"""Update last token refresh timestamp."""
		self.db_set("last_token_refresh", frappe.utils.now(), update_modified=False)

	@staticmethod
	def get_active_settings() -> Optional["GitHubAppSettings"]:
		"""Get the active GitHub App Settings.

		Returns:
			Active GitHubAppSettings document or None
		"""
		settings_name = frappe.db.get_value("GitHub App Settings", {"is_active": 1}, "name")
		if settings_name:
			return frappe.get_doc("GitHub App Settings", settings_name)
		return None


def get_github_settings() -> Optional[GitHubAppSettings]:
	"""Helper function to get active GitHub settings.

	Returns:
		Active GitHubAppSettings document or None
	"""
	return GitHubAppSettings.get_active_settings()
