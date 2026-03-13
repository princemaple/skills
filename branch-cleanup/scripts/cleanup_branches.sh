#!/usr/bin/env bash
# Cleanup merged branches (local + remote) for a git repo.
# Usage: cleanup_branches.sh <repo-path> [--dry-run]
#
# Steps:
# 1. git fetch --prune
# 2. Delete local branches whose remote tracking branch is gone
# 3. For remaining local branches with active remotes, check if PR was merged via gh
# 4. Delete those local + remote branches

set -euo pipefail

REPO="$1"
DRY_RUN="${2:-}"
MAIN_BRANCH="main"

cd "$REPO"
REPO_NAME=$(basename "$REPO")

echo "=== $REPO_NAME ==="

# Fetch and prune stale remote refs
git fetch --prune --quiet

# Determine protected branches
PROTECTED="main|master|develop|staging|production"

# Collect all local branches except current and protected
BRANCHES=()
while IFS= read -r b; do
  b=$(echo "$b" | xargs)  # trim whitespace
  [[ -z "$b" ]] && continue
  BRANCHES+=("$b")
done < <(git branch | grep -vE "^\*" | grep -vE "^[[:space:]]*(${PROTECTED})$")

if [[ ${#BRANCHES[@]} -eq 0 ]]; then
  echo "  No branches to clean up."
  exit 0
fi

DELETED_LOCAL=()
DELETED_REMOTE=()
KEPT=()

for branch in "${BRANCHES[@]}"; do
  HAS_REMOTE=false
  if git branch -r | grep -q "origin/${branch}$"; then
    HAS_REMOTE=true
  fi

  if [[ "$HAS_REMOTE" == "false" ]]; then
    # Remote is gone — branch was likely merged via squash/rebase
    echo "  Deleting local '$branch' (remote gone)"
    if [[ "$DRY_RUN" != "--dry-run" ]]; then
      git branch -D "$branch" 2>/dev/null || true
    fi
    DELETED_LOCAL+=("$branch")
  else
    # Remote exists — check if PR was merged
    MERGED=$(gh pr list --state merged --head "$branch" --json number --jq 'length' 2>/dev/null || echo "0")
    if [[ "$MERGED" -gt 0 ]]; then
      echo "  Deleting '$branch' (PR merged, local + remote)"
      if [[ "$DRY_RUN" != "--dry-run" ]]; then
        git branch -D "$branch" 2>/dev/null || true
        git push origin --delete "$branch" 2>/dev/null || true
      fi
      DELETED_LOCAL+=("$branch")
      DELETED_REMOTE+=("$branch")
    else
      echo "  Keeping '$branch' (active, no merged PR)"
      KEPT+=("$branch")
    fi
  fi
done

echo ""
echo "  Deleted: ${#DELETED_LOCAL[@]} local, ${#DELETED_REMOTE[@]} remote"
echo "  Kept: ${#KEPT[@]}"
