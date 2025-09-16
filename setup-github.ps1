# GitHub Repository Setup Script for BillingTest
param(
    [Parameter(Mandatory=$true, HelpMessage="Enter your GitHub username")]
    [string]$GitHubUsername,
    
    [Parameter(HelpMessage="Repository visibility (public/private)")]
    [ValidateSet("public", "private")]
    [string]$Visibility = "public",
    
    [Parameter(HelpMessage="Skip push to remote")]
    [switch]$SkipPush
)

Write-Host "`n🚀 BillingTest GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "=====================================`n" -ForegroundColor Cyan

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git detected: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check current directory
$currentDir = Get-Location
Write-Host "📁 Current directory: $currentDir" -ForegroundColor Yellow

# Confirm this is the right directory
$projectFiles = @("pyproject.toml", "Dockerfile", "README.md")
$foundFiles = $projectFiles | Where-Object { Test-Path $_ }

if ($foundFiles.Count -eq 0) {
    Write-Host "❌ This doesn't appear to be the BillingTest project directory." -ForegroundColor Red
    Write-Host "   Expected files not found: $($projectFiles -join ', ')" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ BillingTest project detected" -ForegroundColor Green

# Initialize git if needed
if (-not (Test-Path .git)) {
    Write-Host "`n📝 Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Check for existing remote
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "`n⚠️  Existing remote detected: $existingRemote" -ForegroundColor Yellow
    $response = Read-Host "Do you want to replace it? (y/n)"
    if ($response -eq 'y') {
        git remote remove origin
        Write-Host "✅ Existing remote removed" -ForegroundColor Green
    } else {
        Write-Host "❌ Setup cancelled" -ForegroundColor Red
        exit 0
    }
}

# Update README.md with correct username
Write-Host "`n📝 Updating README.md with your username..." -ForegroundColor Yellow
$readmePath = "README.md"
if (Test-Path $readmePath) {
    $content = Get-Content $readmePath -Raw
    $updatedContent = $content -replace "johanna-II/BillingTest", "$GitHubUsername/BillingTest"
    $updatedContent | Set-Content $readmePath -NoNewline
    Write-Host "✅ README.md updated" -ForegroundColor Green
}

# Create .gitignore if it doesn't exist
if (-not (Test-Path .gitignore)) {
    Write-Host "`n📝 Creating .gitignore..." -ForegroundColor Yellow
    @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/
*.cover
.coverage.*
report/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Secrets
.env
*.pem
*.key

# Logs
*.log

# Poetry
poetry.lock
"@ | Set-Content .gitignore
    Write-Host "✅ .gitignore created" -ForegroundColor Green
}

# Stage all files
Write-Host "`n📦 Staging files..." -ForegroundColor Yellow
git add .

# Show status
Write-Host "`n📊 Git status:" -ForegroundColor Yellow
git status --short

# Commit
$commitMessage = "Initial commit: Billing Test Suite with GitHub Actions CI/CD"
Write-Host "`n💾 Creating commit..." -ForegroundColor Yellow
git commit -m $commitMessage 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  No changes to commit or commit failed" -ForegroundColor Yellow
}

# Set main branch
Write-Host "`n🌿 Setting main branch..." -ForegroundColor Yellow
git branch -M main

# Add remote
$repoUrl = "https://github.com/$GitHubUsername/BillingTest.git"
Write-Host "`n🔗 Adding remote repository..." -ForegroundColor Yellow
Write-Host "   URL: $repoUrl" -ForegroundColor Cyan
git remote add origin $repoUrl
Write-Host "✅ Remote added successfully" -ForegroundColor Green

# Push to remote
if (-not $SkipPush) {
    Write-Host "`n🚀 Ready to push to GitHub!" -ForegroundColor Green
    Write-Host "`n⚠️  Before pushing, make sure you have:" -ForegroundColor Yellow
    Write-Host "   1. Created the repository on GitHub (https://github.com/new)" -ForegroundColor White
    Write-Host "   2. Generated a Personal Access Token if using HTTPS" -ForegroundColor White
    Write-Host "      (Settings → Developer settings → Personal access tokens)" -ForegroundColor Gray
    Write-Host "`n📝 Repository details:" -ForegroundColor Cyan
    Write-Host "   Name: BillingTest" -ForegroundColor White
    Write-Host "   Visibility: $Visibility" -ForegroundColor White
    Write-Host "   Initialize: DO NOT check any boxes (no README, .gitignore, or license)" -ForegroundColor Yellow
    
    $response = Read-Host "`nHave you created the repository on GitHub? (y/n)"
    if ($response -eq 'y') {
        Write-Host "`n🔄 Pushing to GitHub..." -ForegroundColor Yellow
        Write-Host "   When prompted:" -ForegroundColor Cyan
        Write-Host "   Username: $GitHubUsername" -ForegroundColor White
        Write-Host "   Password: [Your Personal Access Token]" -ForegroundColor White
        
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host "`n🎉 Your repository is now available at:" -ForegroundColor Cyan
            Write-Host "   https://github.com/$GitHubUsername/BillingTest" -ForegroundColor White
            
            Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
            Write-Host "   1. Add secrets in repository settings (ALPHA_KR_CONFIG, etc.)" -ForegroundColor White
            Write-Host "   2. Check the Actions tab to see your workflows" -ForegroundColor White
            Write-Host "   3. Try running the Billing Test Suite workflow manually" -ForegroundColor White
        } else {
            Write-Host "`n❌ Push failed. Common issues:" -ForegroundColor Red
            Write-Host "   - Repository doesn't exist on GitHub" -ForegroundColor Yellow
            Write-Host "   - Authentication failed (use Personal Access Token, not password)" -ForegroundColor Yellow
            Write-Host "   - Repository name mismatch" -ForegroundColor Yellow
            Write-Host "`nYou can try pushing manually with:" -ForegroundColor Cyan
            Write-Host "   git push -u origin main" -ForegroundColor White
        }
    } else {
        Write-Host "`n📝 Skipping push. When you're ready, run:" -ForegroundColor Yellow
        Write-Host "   git push -u origin main" -ForegroundColor White
    }
} else {
    Write-Host "`n📝 Skipping push (--SkipPush flag set)" -ForegroundColor Yellow
    Write-Host "When you're ready, run:" -ForegroundColor Cyan
    Write-Host "   git push -u origin main" -ForegroundColor White
}

Write-Host "`n✨ Setup complete!" -ForegroundColor Green
