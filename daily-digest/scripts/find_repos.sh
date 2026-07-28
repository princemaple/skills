#!/usr/bin/env bash
# Find all git repositories under a root directory (default: ~/code).
# Prints one absolute repo path per line.
set -euo pipefail

ROOT="${1:-$HOME/code}"

find "$ROOT" -maxdepth 3 -type d -name ".git" 2>/dev/null | while read -r gitdir; do
  dirname "$gitdir"
done | sort
