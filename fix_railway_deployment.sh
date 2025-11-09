#!/bin/bash
# Railway Deployment Fix Script

echo "🔧 Fixing Railway Deployment Structure"
echo "======================================="

echo "Step 1: Remove existing git (if any)"
rm -rf .git

echo "Step 2: Initialize fresh git repository"
git init

echo "Step 3: Add all files to repository"
git add .

echo "Step 4: Create initial commit"
git commit -m "Flask gaming platform ready for Railway deployment"

echo "Step 5: Instructions for GitHub"
echo ""
echo "Now create a NEW GitHub repository and run:"
echo "git remote add origin https://github.com/YOURUSERNAME/NEWREPO.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "Then redeploy on Railway using the new repository"
echo ""
echo "✅ Repository structure fixed!"