# GitHub Manager for Frappe v15

A production-ready Frappe app that allows you to manage GitHub operations directly from Frappe ERP without visiting github.com.

## 🚀 Features

### 🔐 **Secure Authentication**
- GitHub App authentication (NOT personal access tokens)
- Auto-refreshing JWT tokens
- Secure credential storage using Frappe Password fields
- Multi-org and multi-repo support
- Rate limit tracking and management

### 📦 **Repository Management**
- ✅ Create new repositories (public/private)
- ✅ Delete repositories
- ✅ List repositories (org & user)
- ✅ Repository visibility controls
- ✅ Sync repository metadata
- ✅ View repository statistics (stars, forks, issues)

### 🔀 **Pull Request Management**
- ✅ Create pull requests (source → target branch)
- ✅ List pull requests
- ✅ Merge PRs (merge / squash / rebase)
- ✅ Close pull requests
- ✅ Track PR statistics (commits, additions, deletions)
- ✅ Draft PR support

### 🌿 **Branch Management**
- ✅ List branches
- ✅ Create branches
- ✅ Delete branches (with protected branch checks)

### 🏷️ **Release Management**
- ✅ Create releases
- ✅ Attach release notes
- ✅ List releases
- ✅ Delete releases
- ✅ Draft and pre-release support

### 🐛 **Issue Management** (Bonus)
- ✅ Create issues
- ✅ Assign users
- ✅ Add labels
- ✅ Close issues
- ✅ Sync issue comments count

### 📊 **Modern Dashboard UI**
- Interactive GitHub-like dashboard
- Real-time statistics cards
- Recent activity feeds
- Quick action buttons
- Responsive design

### 🔄 **Background Jobs**
- Automatic hourly sync of open PRs
- Daily repository sync
- Manual sync options for all resources
- Queued background processing using `frappe.enqueue`

### 🪝 **Webhook Support**
- Push events
- Pull request events (opened, closed, merged)
- Release events
- Issue events
- Repository events
- HMAC signature verification

### 🔒 **Role-Based Permissions**
- **GitHub Admin**: Full access to all operations
- **GitHub Maintainer**: Create, update, and delete permissions
- **GitHub Viewer**: Read-only access

### 📝 **Audit Logging**
- Track all GitHub API actions
- Request/response logging
- Error tracking
- User and IP tracking

## 📥 Installation

### Prerequisites
- Frappe v15
- Python 3.11+
- GitHub App credentials

### Step 1: Install the App

```bash
cd /path/to/frappe-bench
bench get-app github_manager
bench --site your-site.local install-app github_manager
```

### Step 2: Install Required Python Packages

```bash
pip install PyJWT cryptography requests
```

### Step 3: Migrate and Build

```bash
bench --site your-site.local migrate
bench build --app github_manager
bench restart
```

## ⚙️ Configuration

### Setting up GitHub App

1. **Create a GitHub App**
   - Go to GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
   - Set permissions: Contents, Issues, Pull requests (Read & Write)
   - Generate and download private key (.pem file)

2. **Configure in Frappe**
   - Go to: **GitHub Manager → GitHub App Settings**
   - Enter: App ID, Installation ID, Private Key, Webhook Secret
   - Mark as Active

3. **Assign Roles**
   - Add `GitHub Admin`, `GitHub Maintainer`, or `GitHub Viewer` roles to users

## 📖 Usage

### Accessing Dashboard
Navigate to: `https://your-site.com/app/github`

### API Examples

**Create Repository:**
```python
frappe.call(
    method='github_manager.github_manager.github.repository.create_repository',
    args={'name': 'my-repo', 'is_private': 1}
)
```

**Create Pull Request:**
```python
frappe.call(
    method='github_manager.github_manager.github.pull_request.create_pull_request',
    args={
        'repository': 'owner/repo',
        'title': 'Feature: New feature',
        'head': 'feature-branch',
        'base': 'main'
    }
)
```

## 🏗️ Architecture

```
github_manager/
├── github_manager/
│   ├── doctype/              # Core DocTypes
│   ├── github/               # API layer
│   ├── www/github/           # Dashboard UI
│   ├── hooks.py              # Frappe hooks
│   └── install.py            # Installation script
```

## 🔒 Security

- GitHub App authentication
- JWT auto-refresh
- Encrypted credential storage
- Webhook signature verification
- Role-based access control
- Complete audit logging

## 📝 License

MIT License

## 👥 Credits

Developed by **Dexciss Technology**
