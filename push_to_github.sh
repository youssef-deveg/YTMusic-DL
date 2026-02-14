#!/bin/bash
# Script to push YouTube Music Downloader to GitHub
# Run this script after creating the GitHub repository

echo "====================================="
echo "Pushing to GitHub Repository"
echo "====================================="

# Repository details
REPO_URL="https://github.com/20Youssef10/YT-DL.git"
PROJECT_DIR="/storage/emulated/0/Python Projects/Youtube Music Downloader"

cd "$PROJECT_DIR"

echo ""
echo "Step 1: Setting up remote..."
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"

echo ""
echo "Step 2: Setting branch name..."
git branch -M main

echo ""
echo "Step 3: Checking authentication..."
echo ""
echo "You need to authenticate with GitHub."
echo "Options:"
echo "  1. Use GitHub CLI (gh): Install and run 'gh auth login'"
echo "  2. Use Personal Access Token: Set up a token at github.com/settings/tokens"
echo "  3. Use SSH key: Generate SSH key and add to GitHub"
echo ""

# Check if gh is installed
if command -v gh &> /dev/null; then
    echo "GitHub CLI detected! Attempting authentication..."
    if ! gh auth status &> /dev/null; then
        echo "Please login first: gh auth login"
        gh auth login
    fi
    
    echo ""
    echo "Creating repository if it doesn't exist..."
    gh repo create 20Youssef10/YT-DL --public --source=. --remote=origin --push || true
    
    echo ""
    echo "Pushing code..."
    git push -u origin main
else
    echo "GitHub CLI not found. Please manually push using:"
    echo "  git push -u origin main"
    echo ""
    echo "Or install GitHub CLI:"
    echo "  https://cli.github.com/"
fi

echo ""
echo "====================================="
echo "Repository URL: $REPO_URL"
echo "====================================="
