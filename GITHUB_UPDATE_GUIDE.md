# 🚀 GitHub Auto-Update System Guide

## Overview
Your CMS now automatically checks GitHub releases for updates. When you release a new version on GitHub, **all CMS installations worldwide will automatically detect it** and notify users to update.

## 🔧 How It Works

### 1. **For You (Developer)**
```bash
# Step 1: Update your code
git add .
git commit -m "New features and improvements"

# Step 2: Create a release tag
git tag v1.1.0
git push origin v1.1.0

# Step 3: GitHub automatically creates a release package
# The workflow in .github/workflows/release.yml runs automatically
```

### 2. **For Users (Automatic)**
- Every CMS installation checks GitHub daily for new releases
- Users get notified in their admin panel: "Update Available"
- One-click update button downloads and installs from GitHub
- Automatic backup before update with rollback option

## 📋 Quick Setup

### 1. Install Required Package
```bash
pip install packaging requests
```

### 2. Run Migration (if needed)
```bash
python manage.py makemigrations updates
python manage.py migrate
```

### 3. Test the System
```bash
# Check for updates manually
python manage.py check_github_updates

# Test with force flag
python manage.py check_github_updates --force
```

## 🎯 Release Process

### Method 1: Via GitHub Web Interface
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag: `v1.1.0` (use semantic versioning)
4. Title: `"Ecom CMS 1.1.0"`
5. Description: Write your release notes
6. Click "Publish release"
7. **✅ All CMS sites will detect this within 24 hours**

### Method 2: Via Command Line
```bash
# Create and push tag
git tag v1.1.0
git push origin v1.1.0

# GitHub workflow automatically creates the release
```

### Method 3: Using GitHub CLI
```bash
# Create release with notes
gh release create v1.1.0 --title "Ecom CMS 1.1.0" --notes "Bug fixes and new features"
```

## ⚙️ Configuration

### Admin Panel Settings
Go to **Admin → Updates → Update Settings**:

- ✅ **Auto-check enabled**: Check GitHub daily
- ⏰ **Check frequency**: Daily/Weekly/Monthly  
- 🔄 **Auto-install critical updates**: For security patches
- 💾 **Backup before update**: Always recommended
- 🔔 **Beta updates**: Include pre-releases

### GitHub Token (Optional but Recommended)
Add to `config/settings.py`:
```python
# Higher API rate limits (5000/hour instead of 60/hour)
GITHUB_TOKEN = 'your_github_token_here'
```

## 🔍 Update Detection

### What CMS Sites Check:
- **Repository**: `studsu/ecom_CMS` (update in `core/github_updater.py` if different)
- **API Endpoint**: `https://api.github.com/repos/studsu/ecom_CMS/releases/latest`
- **Version Format**: Tags like `v1.0.0`, `v1.1.0`, `v2.0.0`
- **Update Frequency**: Every 24 hours (configurable)

### Critical Updates
Mark releases as "critical" by including keywords in release notes:
- `security`, `critical`, `urgent`, `hotfix`, `vulnerability`, `exploit`, `patch`

**Critical updates can auto-install** if enabled in settings.

## 📦 Release Types

### Stable Releases
```bash
git tag v1.1.0        # Stable release
```
- Available to all users
- Auto-install if critical

### Pre-releases (Beta)
```bash
git tag v1.1.0-beta    # Pre-release
```
- Only visible if "Beta updates" enabled
- For testing new features

## 🔄 User Experience

### What Users See:
1. **Notification**: "Update Available: Version 1.1.0"
2. **Admin Dashboard**: Red notification badge
3. **Update Details**: Release notes, file size, type
4. **One-Click Install**: "Update Now" button
5. **Progress Tracking**: Real-time update progress
6. **Backup & Rollback**: Automatic backup with restore option

### Update Process:
```
Check → Notify → Backup → Download → Install → Migrate → Complete
```

## 🛡️ Security Features

- ✅ **HTTPS Downloads**: All downloads from GitHub use HTTPS
- ✅ **Checksum Verification**: File integrity checking
- ✅ **Automatic Backups**: Before every update
- ✅ **Admin-Only Access**: Only admin users can update
- ✅ **Rollback System**: Restore previous version if needed

## 📊 Monitoring

### Check Update Logs
```bash
# View recent checks
python manage.py shell -c "
from updates.models import UpdateCheck
for check in UpdateCheck.objects.all()[:5]:
    print(f'{check.check_date}: {check.current_version} -> {check.latest_version}')
"
```

### View Available Updates
Go to **Admin → Updates → Available Updates**

### Check Notifications
Go to **Admin → Updates → Update Notifications**

## 🚨 Troubleshooting

### "No updates found" but release exists
- Check repository name in `core/github_updater.py`
- Verify tag format: `v1.0.0` not `1.0.0`
- Check GitHub API rate limits

### Update check fails
```bash
# Test GitHub connectivity
python manage.py check_github_updates --force

# Check GitHub API response
curl https://api.github.com/repos/studsu/ecom_CMS/releases/latest
```

### Rate limit exceeded
- Add GitHub token to `settings.py`
- Reduce check frequency in admin settings

## 🎉 Example Workflow

### Your Release Process:
```bash
# 1. Develop new features
git add . && git commit -m "Add new payment gateway"

# 2. Create release
git tag v1.2.0
git push origin v1.2.0

# 3. Add release notes on GitHub
# GitHub workflow automatically creates package

# 4. Within 24 hours, all users see:
#    "Update Available: Version 1.2.0"
```

### User Experience:
1. User logs into admin panel
2. Sees: 🔔 "Update Available: Version 1.2.0"
3. Clicks "View Updates"
4. Reads release notes: "Add new payment gateway"
5. Clicks "Update Now"
6. System: Backup → Download → Install → Complete
7. User sees: "Successfully updated to 1.2.0"

## 🔧 Customization

### Change Repository
Edit `core/github_updater.py`:
```python
self.github_owner = "your_username"
self.github_repo = "your_repo_name"
```

### Custom Update Frequency
Add to crontab:
```bash
# Check every 6 hours
0 */6 * * * cd /path/to/cms && python manage.py check_github_updates
```

### Email Notifications
Set email in **Admin → Updates → Update Settings**

This system provides **WordPress-level auto-updates** while maintaining full control through GitHub releases! 🎉