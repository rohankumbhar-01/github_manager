# GitHub Manager - Installation Checklist

Use this checklist to ensure proper installation and configuration.

## ✅ Pre-Installation

- [ ] Frappe v15 is installed and running
- [ ] Python 3.11+ is available
- [ ] You have access to GitHub organization/account
- [ ] You have admin rights on Frappe site

## ✅ Installation Steps

### 1. Install App
```bash
cd /path/to/frappe-bench
bench --site your-site.local install-app github_manager
```
- [ ] App installed successfully

### 2. Install Python Dependencies
```bash
./env/bin/pip install PyJWT cryptography requests
```
- [ ] PyJWT installed
- [ ] cryptography installed
- [ ] requests installed

### 3. Run Migration
```bash
bench --site your-site.local migrate
```
- [ ] Migration completed without errors
- [ ] All 7 DocTypes created:
  - [ ] GitHub App Settings
  - [ ] GitHub Organization
  - [ ] GitHub Repository
  - [ ] GitHub Pull Request
  - [ ] GitHub Release
  - [ ] GitHub Issue
  - [ ] GitHub Audit Log

### 4. Build Assets
```bash
bench build --app github_manager
```
- [ ] Build completed successfully
- [ ] No JavaScript errors

### 5. Restart Services
```bash
bench restart
```
- [ ] Services restarted successfully

## ✅ GitHub App Configuration

### 1. Create GitHub App
Go to: https://github.com/settings/apps

- [ ] Created new GitHub App
- [ ] Set App name
- [ ] Set Homepage URL
- [ ] Set Webhook URL: `https://your-site.com/api/method/github_manager.github.webhooks.handle_webhook`
- [ ] Generated and saved Webhook secret

### 2. Set Permissions
Repository permissions:
- [ ] Contents: Read & Write
- [ ] Issues: Read & Write
- [ ] Pull requests: Read & Write
- [ ] Metadata: Read-only

### 3. Generate Private Key
- [ ] Generated private key
- [ ] Downloaded .pem file
- [ ] Saved file securely

### 4. Install App
- [ ] Installed GitHub App on organization/account
- [ ] Noted Installation ID from URL

### 5. Collect Credentials
You should have:
- [ ] App ID (number from settings page)
- [ ] Installation ID (number from URL)
- [ ] Private Key (.pem file contents)
- [ ] Webhook Secret (string you generated)

## ✅ Frappe Configuration

### 1. Create GitHub App Settings Record
Navigate to: `https://your-site.com/app/github-app-settings`

- [ ] Created new GitHub App Settings
- [ ] Entered App Name
- [ ] Entered App ID
- [ ] Entered Installation ID
- [ ] Pasted entire Private Key (including BEGIN/END lines)
- [ ] Entered Webhook Secret
- [ ] Checked "Is Active"
- [ ] Saved successfully

### 2. Verify Settings
- [ ] No errors on save
- [ ] Settings record exists
- [ ] Is Active is checked

## ✅ User Permissions

### Assign Roles to Users
For each user who needs access:

- [ ] Opened User record
- [ ] Added appropriate role:
  - [ ] GitHub Admin (full access)
  - [ ] GitHub Maintainer (create/edit)
  - [ ] GitHub Viewer (read-only)
- [ ] Saved user record

## ✅ Testing

### 1. Access Dashboard
Navigate to: `https://your-site.com/app/github`

- [ ] Dashboard loads without errors
- [ ] Statistics cards display (may show 0)
- [ ] Action buttons visible

### 2. Test Repository Sync
- [ ] Clicked "Sync Repositories"
- [ ] Received success message
- [ ] Refreshed page
- [ ] Repository count updated

### 3. Test Repository Creation
- [ ] Clicked "Create Repository"
- [ ] Filled in form:
  - Name: `test-github-manager`
  - Description: `Test repository`
  - Private: checked
- [ ] Clicked Create
- [ ] Received success message
- [ ] Verified repository exists on GitHub

### 4. Test API Calls
Open Frappe console: `bench --site your-site.local console`

```python
# Test repository stats
import frappe
stats = frappe.call('github_manager.github.repository.get_repository_stats')
print(stats)
```

- [ ] API call successful
- [ ] Stats returned

### 5. Check Audit Log
Navigate to: `https://your-site.com/app/github-audit-log`

- [ ] Audit log entries exist
- [ ] Actions are logged
- [ ] Request/response data visible

## ✅ Webhooks (Optional but Recommended)

### 1. Configure Webhook
In GitHub App settings:
- [ ] Webhook URL is set
- [ ] Webhook secret is set
- [ ] SSL verification enabled

### 2. Test Webhook
- [ ] Created a test PR on GitHub
- [ ] Checked GitHub webhook deliveries
- [ ] Delivery successful (green checkmark)
- [ ] PR synced to Frappe

## ✅ Scheduled Jobs

### Verify Scheduler is Running
```bash
bench --site your-site.local doctor
```

- [ ] Scheduler is running
- [ ] No errors in output

### Check Scheduled Jobs
- [ ] Hourly job configured (sync open PRs)
- [ ] Daily job configured (sync repositories)

## ✅ Production Readiness (if deploying to production)

### Security
- [ ] SSL certificate is valid
- [ ] Webhook URL accessible from internet
- [ ] Strong webhook secret used (32+ characters)
- [ ] Private key stored securely
- [ ] Appropriate firewall rules in place

### Monitoring
- [ ] Error log monitoring configured
- [ ] Audit log review process in place
- [ ] Rate limit monitoring enabled

### Backup
- [ ] Database backup strategy in place
- [ ] GitHub App credentials backed up securely

## ✅ Common Issues Resolved

- [ ] No "module not found" errors
- [ ] No "permission denied" errors
- [ ] No "invalid signature" webhook errors
- [ ] No "rate limit exceeded" errors

## 📝 Post-Installation Notes

**Installation Date:** _______________

**Installed By:** _______________

**GitHub App Name:** _______________

**App ID:** _______________

**Installation ID:** _______________

**Site URL:** _______________

**Webhook URL:** _______________

**Roles Assigned:**
- GitHub Admin: _______________
- GitHub Maintainer: _______________
- GitHub Viewer: _______________

## 🎉 Success Criteria

Your installation is complete when:

✅ All migration steps completed without errors
✅ Dashboard loads and displays data
✅ Can create repositories from Frappe
✅ Sync operations work
✅ Audit log captures actions
✅ Users have appropriate roles
✅ Webhooks deliver successfully (if configured)

## 📞 Support

If you encounter issues:

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section
2. Review Frappe error logs: `bench --site your-site.local logs`
3. Check GitHub webhook delivery logs
4. Review audit log for error messages

---

**Congratulations!** Your GitHub Manager app is now installed and ready to use! 🚀
