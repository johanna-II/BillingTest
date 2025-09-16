# GitHub Repository Setup Guide

## Step 1: Create New Repository on GitHub

1. **Login to your GitHub account**
   - Go to https://github.com
   - Sign in with your credentials

2. **Create new repository**
   - Click the "+" icon in the top right corner
   - Select "New repository"
   - Repository settings:
     - **Repository name**: `BillingTest`
     - **Description**: "Billing Automation Test Suite for payment module verification"
     - **Visibility**: Choose Public or Private
     - **Initialize repository**: ❌ Do NOT check any boxes (no README, .gitignore, or license)
   - Click "Create repository"

## Step 2: Prepare Your Local Repository

Open PowerShell or Command Prompt in your project directory:

```powershell
# Navigate to your project
cd C:\Users\lucyk4t\Documents\BillingTest

# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Migrated from Jenkins to GitHub Actions"
```

## Step 3: Connect to GitHub Repository

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username:

```powershell
# Add GitHub repository as remote
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/BillingTest.git

# Verify remote was added
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: If You Get Authentication Error

GitHub now requires personal access tokens instead of passwords:

1. **Generate Personal Access Token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token"
   - Give it a name (e.g., "BillingTest Upload")
   - Select scopes: `repo` (full control)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Use token for authentication**
   ```powershell
   # When prompted for password, paste your token instead
   git push -u origin main
   # Username: YOUR_GITHUB_USERNAME
   # Password: YOUR_PERSONAL_ACCESS_TOKEN
   ```

## Step 5: Alternative - Using GitHub Desktop

If you prefer a GUI approach:

1. Download [GitHub Desktop](https://desktop.github.com/)
2. Sign in with your GitHub account
3. Click "Add" → "Add Existing Repository"
4. Browse to `C:\Users\lucyk4t\Documents\BillingTest`
5. Click "Publish repository"
6. Uncheck "Keep this code private" if you want it public
7. Click "Publish repository"

## Step 6: Set Up Repository Settings

After pushing the code:

1. **Add Secrets** (Settings → Secrets and variables → Actions)
   ```
   ALPHA_KR_CONFIG
   ALPHA_JP_CONFIG
   ALPHA_ETC_CONFIG
   ```

2. **Enable GitHub Actions** (Should be automatic, but check Actions tab)

3. **Update README.md badges**
   - Replace `johanna-II` with your GitHub username in all badge URLs

4. **Set up branch protection** (Settings → Branches)
   - Add rule for `main` branch
   - Require pull request reviews
   - Require status checks to pass

## Step 7: Verify Everything Works

1. **Check GitHub Actions**
   - Go to Actions tab
   - You should see the workflows
   - Try running "Billing Test Suite" manually

2. **Update remote URLs in workflows**
   ```bash
   # Update these files with your username:
   # - README.md (badge URLs)
   # - .github/workflows/*.yml (if any hardcoded URLs)
   ```

## Common Issues and Solutions

### Issue: "fatal: remote origin already exists"
```powershell
# Remove existing remote and add new one
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/BillingTest.git
```

### Issue: "Permission denied (publickey)"
```powershell
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/YOUR_USERNAME/BillingTest.git
```

### Issue: Large files (>100MB)
```powershell
# Use Git LFS for large files
git lfs track "*.pkl"
git lfs track "*.h5"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### Issue: Pushing fails due to large history
```powershell
# Create fresh repository without history
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/BillingTest.git
git push -u origin main --force
```

## Quick Setup Script

Save this as `setup-github.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername
)

Write-Host "Setting up GitHub repository for $GitHubUsername..." -ForegroundColor Green

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Billing Test Suite with GitHub Actions"

# Add remote
$repoUrl = "https://github.com/$GitHubUsername/BillingTest.git"
git remote add origin $repoUrl

Write-Host "Remote added: $repoUrl" -ForegroundColor Yellow
Write-Host "Now run: git push -u origin main" -ForegroundColor Yellow
Write-Host "You'll be prompted for your GitHub username and personal access token" -ForegroundColor Yellow
```

Run it:
```powershell
.\setup-github.ps1 -GitHubUsername YOUR_USERNAME
```

## Next Steps

1. **Test the workflows**
   - Push a small change to trigger CI
   - Run manual billing test

2. **Set up documentation**
   - Consider GitHub Pages for test reports
   - Add wiki for detailed documentation

3. **Invite collaborators**
   - Settings → Manage access → Invite collaborators

4. **Set up integrations**
   - Slack notifications
   - Issue templates
   - PR templates

Good luck with your new repository! 🚀
