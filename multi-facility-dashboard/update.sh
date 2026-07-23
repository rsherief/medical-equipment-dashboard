#!/usr/bin/env bash
# Rebuild the dashboard from the Excel files in data/ and publish it.
# Usage: ./update.sh [commit message]
set -e
cd "$(dirname "$0")"

python3 build.py

if git diff --quiet && git diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi

git add -A
git commit -m "${1:-Data update $(date +%F)}"
git push
echo "Published. GitHub Pages updates in ~1 minute."
