#!/bin/bash

echo "=== Publishing Latin Vocab Trainer to GitHub ==="
echo ""

if [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_USERNAME and GITHUB_TOKEN environment variables are required"
    echo ""
    echo "Set them with:"
    echo "  export GITHUB_USERNAME=yourusername"
    echo "  export GITHUB_TOKEN=your_personal_access_token"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo"
    exit 1
fi

REPO_NAME="Latin-Vocab-Trainer"
echo "Checking if repository exists..."

if gh repo view "$GITHUB_USERNAME/$REPO_NAME" 2>/dev/null; then
    echo "Repository already exists"
    REPO_EXISTS=true
else
    echo "Creating new repository..."
    gh auth login --with-token <<< "$GITHUB_TOKEN"
    gh repo create "$GITHUB_USERNAME/$REPO_NAME" --public --source=. --description "Latin Vocabulary Trainer - A Flask web application for learning Latin vocabulary"
    REPO_EXISTS=false
fi

echo ""
echo "Pushing to GitHub..."

git init
git add .
git commit -m "Initial commit: Latin Vocab Trainer with production deployment setup"

git branch -M main
git remote add origin "https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com/$GITHUB_USERNAME/$REPO_NAME.git"
git push -u origin main

echo ""
echo "=== Published Successfully ==="
echo "Repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME"