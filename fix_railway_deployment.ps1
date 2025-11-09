# Railway Deployment Fix Script (PowerShell)

Write-Host "🔧 Fixing Railway Deployment Structure" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

Write-Host "Step 1: Remove existing git (if any)" -ForegroundColor Yellow
if (Test-Path ".git") {
    Remove-Item -Recurse -Force ".git"
    Write-Host "✅ Removed existing .git directory" -ForegroundColor Green
}

Write-Host "Step 2: Initialize fresh git repository" -ForegroundColor Yellow
git init

Write-Host "Step 3: Add all files to repository" -ForegroundColor Yellow
git add .

Write-Host "Step 4: Create initial commit" -ForegroundColor Yellow
git commit -m "Flask gaming platform ready for Railway deployment"

Write-Host ""
Write-Host "Step 5: Instructions for GitHub" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to GitHub.com and create a NEW repository (e.g., 'gaming-platform')" -ForegroundColor White
Write-Host "2. Run these commands:" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/YOURUSERNAME/gaming-platform.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Go back to Railway and connect the NEW repository" -ForegroundColor White
Write-Host ""
Write-Host "✅ Repository structure fixed!" -ForegroundColor Green