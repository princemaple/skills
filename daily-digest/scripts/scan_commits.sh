#!/usr/bin/env bash
# Dump commits on the current branch of a repo since a given time, with
# their changed-file list, in a delimited format that's easy to parse.
#
# Usage: scan_commits.sh <repo_path> <since>
#   <since> is anything git's --since understands, e.g. "24 hours ago",
#   "3 days ago", "2026-07-01", "monday".
set -euo pipefail

REPO="$1"
SINCE="$2"

cd "$REPO"

REPO_NAME=$(basename "$REPO")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

echo "@@REPO@@"
echo "$REPO_NAME"
echo "$REPO"
echo "$BRANCH"

git log --since="$SINCE" --no-merges --date=iso-strict \
  --pretty=format:'@@COMMIT@@%n%H%n%ad%n%an%n%s%n%b%n@@FILES@@' \
  --name-status

echo
echo "@@END@@"
