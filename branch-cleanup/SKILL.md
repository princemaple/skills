---
name: branch-cleanup
description: "Clean up merged git branches (local and remote) across one or more repositories. Use when the user asks to clean up branches, delete merged branches, prune stale branches, or tidy up repos. Trigger phrases: 'cleanup branches', 'delete merged branches', 'prune branches', 'clean up repos'."
---

# Branch Cleanup

Clean up merged local and remote branches across multiple git repositories.

## Workflow

1. Parse repo names/paths from the user's request. Repos are typically subdirectories under the current working directory.
2. Run `scripts/cleanup_branches.sh` for each repo in parallel:
   ```bash
   bash <skill-path>/scripts/cleanup_branches.sh /path/to/repo
   ```
3. Report a summary table of what was deleted and kept per repo.

## What the script does

For each repo:
1. `git fetch --prune` to sync remote state
2. Delete local branches whose remote tracking branch is gone (merged via squash/rebase on GitHub)
3. For remaining local branches with active remotes, check `gh pr list --state merged --head <branch>` to see if the PR was merged
4. Delete both local and remote for PR-merged branches
5. Keep branches with no merged PR (still active)

Protected branches (never deleted): `main`, `master`, `develop`, `staging`, `production`.

## Dry run

Add `--dry-run` as second argument to preview without deleting:
```bash
bash <skill-path>/scripts/cleanup_branches.sh /path/to/repo --dry-run
```

## Prerequisites

- `git` and `gh` CLI must be available and authenticated
