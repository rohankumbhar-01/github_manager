# GitHub Manager - Complete Setup Guide

This guide walks you through setting up the GitHub Manager app for Frappe v15 from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [GitHub App Setup](#github-app-setup)
4. [Frappe Configuration](#frappe-configuration)
5. [Testing](#testing)
6. [Webhooks Setup](#webhooks-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Frappe Framework**: v15.x
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Operating System**: Linux, macOS, or Windows with WSL2

### Python Packages
The following packages will be installed:
- `PyJWT>=2.8.0` - For JWT token generation
- `cryptography>=41.0.0` - For RSA key handling
- `requests>=2.31.0` - For HTTP requests

---

## Installation

### Step 1: Get the App

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/your-org/github_manager.git
```

Or if developing locally from this directory:

```bash
cd /path/to/frappe-bench
bench get-app /path/to/github_manager
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
./env/bin/pip install PyJWT cryptography requests

# Or add to your requirements.txt in the app
cd apps/github_manager
echo "PyJWT>=2.8.0" >> requirements.txt
echo "cryptography>=41.0.0" >> requirements.txt
echo "requests>=2.31.0" >> requirements.txt
```

### Step 3: Install on Site

```bash
bench --site your-site.local install-app github_manager
```

### Step 4: Migrate Database

```bash
bench --site your-site.local migrate
```

### Step 5: Build Assets

```bash
bench build --app github_manager
```

### Step 6: Restart

```bash
bench restart
# or if using production
sudo systemctl restart frappe-bench-frappe-web frappe-bench-frappe-schedule frappe-bench-frappe-worker-default
```

---

## GitHub App Setup

### Step 1: Create GitHub App

1. **Navigate to GitHub Settings:**
   - Go to https://github.com/settings/apps
   - Or: Your Profile → Settings → Developer settings → GitHub Apps

2. **Click "New GitHub App"**

3. **Fill in Basic Information:**
   ```
   GitHub App name: Your App Name (e.g., "Frappe GitHub Manager")
   Homepage URL: https://your-frappe-site.com
   Description: Manage GitHub from Frappe ERP
   ```

4. **Set Webhook URL:**
   ```
   Webhook URL: https://your-frappe-site.com/api/method/github_manager.github_manager.github.webhooks.handle_webhook
   Webhook secret: [Generate a strong secret - save this!]

   Example secret generation:
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Set Permissions:**

   **Repository Permissions:**
   - Contents: Read & Write
   - Issues: Read & Write
   - Metadata: Read-only
   - Pull requests: Read & Write

   **Organization Permissions (Optional):**
   - Members: Read-only

6. **Subscribe to Events:**
   - [x] Push
   - [x] Pull request
   - [x] Issues
   - [x] Release
   - [x] Repository

7. **Where can this GitHub App be installed?**
   - Select "Any account" or "Only on this account" based on your needs

8. **Create the App**

### Step 2: Generate Private Key

1. After creating the app, scroll down to **Private keys**
2. Click **"Generate a private key"**
3. A `.pem` file will be downloaded automatically
4. **Save this file securely** - you'll need its contents

### Step 3: Install the GitHub App

1. On your GitHub App settings page, click **"Install App"** in the left sidebar
2. Select the organization or personal account
3. Choose:
   - **All repositories** (recommended for testing), or
   - **Only select repositories**
4. Click **Install**
5. **Note the Installation ID** from the URL:
   ```
   https://github.com/settings/installations/[INSTALLATION_ID]
   ```

### Step 4: Collect Credentials

You should now have:
- ✅ App ID (from App settings page)
- ✅ Installation ID (from installation URL)
- ✅ Private Key (.pem file)
- ✅ Webhook Secret (you generated this)

---

## Frappe Configuration

### Step 1: Access GitHub App Settings

1. Log in to your Frappe site
2. Navigate to:
   ```
   Desk → GitHub Manager → GitHub App Settings
   ```
   Or directly: `https://your-site.com/app/github-app-settings`

3. Click **"New"**

### Step 2: Enter Credentials

Fill in the form:

| Field | Value | Example |
|-------|-------|---------|
| **App Name** | Any identifier | "Production GitHub App" |
| **App ID** | From GitHub App settings | 123456 |
| **Installation ID** | From installation URL | 789012 |
| **Private Key** | Full contents of `.pem` file | -----BEGIN RSA PRIVATE KEY----- ... |
| **Webhook Secret** | Secret you generated | your-webhook-secret |
| **Is Active** | Check this box | ✓ |

**Important:** For Private Key, paste the ENTIRE content of the `.pem` file, including:
```
-----BEGIN RSA PRIVATE KEY-----
[key content]
-----END RSA PRIVATE KEY-----
```

### Step 3: Save Settings

1. Click **Save**
2. If successful, you'll see the record saved
3. The "Last Token Refresh" field will update automatically when the app makes API calls

### Step 4: Assign Roles to Users

1. Go to **User List**: `https://your-site.com/app/user`
2. Edit a user
3. Scroll to **Roles** section
4. Add one of:
   - **GitHub Admin** - Full access (create, delete, manage)
   - **GitHub Maintainer** - Create and update (no delete)
   - **GitHub Viewer** - Read-only access

---

## Testing

### Test 1: Access Dashboard

1. Navigate to: `https://your-site.com/app/github`
2. You should see the GitHub Manager Dashboard
3. Initial stats should show 0 for everything (this is normal)

### Test 2: Sync Repositories

1. On the dashboard, click **"Sync Repositories"**
2. Wait a few seconds
3. Check for success message
4. Refresh page - you should see repository counts

### Test 3: Create a Repository

1. Click **"Create Repository"** on dashboard
2. Fill in:
   - Repository Name: `test-repo`
   - Description: `Test repository from Frappe`
   - Private: ✓
3. Click **Create**
4. Check GitHub to verify repository was created

### Test 4: Create a Pull Request

1. First, create a repository with branches (or use existing one)
2. Use Frappe console:
   ```python
   import frappe

   frappe.call(
       method='github_manager.github_manager.github.pull_request.create_pull_request',
       args={
           'repository': 'owner/test-repo',
           'title': 'Test PR from Frappe',
           'head': 'develop',
           'base': 'main',
           'body': 'This is a test PR created from Frappe'
       }
   )
   ```
3. Check GitHub to verify PR was created

### Test 5: View Audit Log

1. Navigate to: **GitHub Manager → GitHub Audit Log**
2. You should see logs of all actions performed
3. Check for successful operations

---

## Webhooks Setup

### Configure Webhook in GitHub

Your webhook should already be configured, but verify:

1. Go to your GitHub App settings
2. Check **Webhook URL** is set to:
   ```
   https://your-site.com/api/method/github_manager.github_manager.github.webhooks.handle_webhook
   ```
3. **Webhook secret** matches what you entered in Frappe
4. **SSL verification** is enabled (recommended)

### Test Webhook

1. In GitHub App settings, scroll to **Recent Deliveries**
2. Trigger an event (create PR, push code, create issue)
3. Check for successful delivery (green checkmark)
4. If failed:
   - Click on the delivery to see error
   - Common issues:
     - SSL certificate invalid
     - Signature verification failed
     - Site not accessible from internet

### Local Development Webhooks

For local testing, use a tunnel service:

**Using ngrok:**
```bash
ngrok http 8000
# Use the https URL as your webhook URL
https://abc123.ngrok.io/api/method/github_manager.github_manager.github.webhooks.handle_webhook
```

**Using localtunnel:**
```bash
npx localtunnel --port 8000
```

---

## Scheduled Jobs

The app includes automatic syncing:

### Hourly Sync (Open PRs)
Syncs all open pull requests for all repositories.

### Daily Sync (Repositories)
Syncs all repositories from GitHub.

### Check Scheduler Status

```bash
# Check if scheduler is running
bench --site your-site.local doctor

# View scheduled jobs
bench --site your-site.local console
>>> frappe.get_all('Scheduled Job Type', fields=['method', 'frequency'])
```

---

## Troubleshooting

### Issue: "No active GitHub App Settings found"

**Cause:** No active GitHub App Settings record

**Solution:**
1. Go to GitHub App Settings
2. Create a new record
3. Ensure "Is Active" is checked
4. Save

### Issue: "Failed to get access token"

**Cause:** Invalid credentials or expired token

**Solution:**
1. Verify App ID is correct (should be a number)
2. Verify Installation ID is correct
3. Check Private Key format:
   - Must start with `-----BEGIN RSA PRIVATE KEY-----`
   - Must end with `-----END RSA PRIVATE KEY-----`
   - No extra spaces or characters
4. Regenerate private key if needed

### Issue: "Invalid signature" on webhooks

**Cause:** Webhook secret mismatch

**Solution:**
1. Verify webhook secret in GitHub matches Frappe
2. Re-enter webhook secret in both places
3. Test with a new webhook delivery

### Issue: "Rate limit exceeded"

**Cause:** Too many API requests

**Solution:**
1. Wait for rate limit reset (shown in GitHub App Settings)
2. Reduce sync frequency
3. Use multiple GitHub Apps for different orgs

### Issue: "Permission denied" errors

**Cause:** Insufficient permissions for user or GitHub App

**Solution:**
1. Check user has appropriate role (Admin/Maintainer/Viewer)
2. Check GitHub App has required permissions:
   - Contents: Read & Write
   - Issues: Read & Write
   - Pull requests: Read & Write

### Issue: Dashboard not loading

**Cause:** Missing dependencies or build issues

**Solution:**
```bash
# Rebuild assets
bench build --app github_manager

# Clear cache
bench --site your-site.local clear-cache

# Restart
bench restart
```

### Issue: "DocType not found" errors after installation

**Cause:** Migration not completed

**Solution:**
```bash
bench --site your-site.local migrate
bench build
bench restart
```

---

## Advanced Configuration

### Custom Sync Frequency

Edit `hooks.py` to change sync frequency:

```python
scheduler_events = {
    "every_30_minutes": [  # Changed from hourly
        "github_manager.github_manager.github.background_jobs.scheduled_sync_open_prs"
    ],
    "weekly": [  # Changed from daily
        "github_manager.github_manager.github.background_jobs.scheduled_sync_repositories"
    ],
}
```

### Multiple GitHub Apps

You can configure multiple GitHub Apps:

1. Create multiple GitHub App Settings records
2. Only mark ONE as "Is Active" at a time
3. Switch between them as needed

Or modify the code to support organization-based routing.

---

## Production Checklist

Before going to production:

- [ ] SSL certificate is valid and configured
- [ ] Webhook URL is accessible from internet
- [ ] Firewall allows GitHub webhook IPs
- [ ] Strong webhook secret is used
- [ ] Private key is stored securely
- [ ] Appropriate roles assigned to users
- [ ] Audit logging is enabled
- [ ] Scheduled jobs are running
- [ ] Error logs are monitored
- [ ] Backup strategy is in place

---

## Support

For issues:
1. Check Frappe error logs: `bench --site your-site.local logs`
2. Check GitHub webhook delivery logs
3. Review audit log in Frappe
4. Create an issue on GitHub repository

---

## Quick Reference

### Important URLs
- Dashboard: `/app/github`
- Settings: `/app/github-app-settings`
- Repositories: `/app/github-repository`
- Pull Requests: `/app/github-pull-request`
- Audit Log: `/app/github-audit-log`

### Webhook URL
```
https://your-site.com/api/method/github_manager.github_manager.github.webhooks.handle_webhook
```

### Console Commands
```python
# Get active settings
from github_manager.github_manager.doctype.github_app_settings.github_app_settings import get_github_settings
settings = get_github_settings()

# Manual sync
from github_manager.github_manager.github.repository import sync_repositories
sync_repositories()

# Create repo
from github_manager.github_manager.github.repository import create_repository
create_repository(name='test', description='Test', is_private=1)
```

---

**Last Updated:** January 2026
**Version:** 1.0.0
