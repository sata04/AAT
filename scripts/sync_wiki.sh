#!/bin/bash
set -e

# Wiki Sync Script for AAT Project
# This script syncs the wiki/ directory from the main repository to the GitHub Wiki repository

WIKI_REPO_URL="$1"
GITHUB_TOKEN="$2"
COMMIT_SHA="$3"

# Validate inputs
if [ -z "$WIKI_REPO_URL" ] || [ -z "$GITHUB_TOKEN" ] || [ -z "$COMMIT_SHA" ]; then
    echo "❌ Error: Missing required arguments"
    echo "Usage: $0 <wiki_repo_url> <github_token> <commit_sha>"
    exit 1
fi

# Configure Git
git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

# Clone Wiki repository
echo "📥 Cloning Wiki repository..."
WIKI_DIR="wiki-repo"
git clone "https://x-access-token:${GITHUB_TOKEN}@${WIKI_REPO_URL}" "$WIKI_DIR"

# Navigate to wiki directory
cd "$WIKI_DIR"

# Remove all existing files except .git
echo "🧹 Cleaning existing Wiki files..."
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

# Copy files from main repository's wiki/ directory
echo "📋 Copying files from wiki/ directory..."
cp -r ../wiki/* .

# Check for changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Changes detected, committing..."
    git add .
    git commit -m "Auto-sync from main repository (commit: ${COMMIT_SHA})"

    echo "🚀 Pushing to Wiki repository..."
    git push origin master

    echo "✅ Wiki successfully synced!"
else
    echo "ℹ️  No changes to sync"
fi

# Cleanup
cd ..
rm -rf "$WIKI_DIR"

echo "🎉 Sync completed successfully"
