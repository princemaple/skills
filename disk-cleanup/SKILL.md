---
name: disk-cleanup
description: Surveys disk usage on the local machine, identifies what's safe to remove (old CLI tool versions, unused nvm/asdf versions, package manager caches, idle node_modules, Docker images/build cache/volumes, stale journal logs, oversized files), and presents a ranked, sized list for the user to choose from before deleting anything. Use this whenever the user asks what's eating their disk space, why disk usage is high or "soaring", how to free up space, wants to clean up their machine, mentions df/du output, a full or nearly-full disk, or asks to prune Docker/node_modules/caches/old versions. Always run the scan and present choices before deleting anything — never clean up disk space unprompted or skip straight to deletion.
---

# Disk Cleanup

A two-phase skill: **scan and report first, delete only what the user explicitly picks.** The scan phase must never delete or modify anything — it only reads. This separation exists because disk cleanup candidates are heterogeneous (some are 100% safe regenerable caches, others are project data or version-manager state the user might still need) and only the user can weigh "will I need this again" tradeoffs for their own machine.

## Phase 1: Scan

Run the bundled survey script, which gathers raw data across all the common cleanup categories in one pass:

```bash
bash ~/.claude/skills/disk-cleanup/scripts/scan.sh
```

(If installed elsewhere, use the actual path to `scripts/scan.sh` alongside this file.)

The script is read-only — it runs `df`, `du`, `docker system df`, `journalctl --disk-usage`, `find`, and process-listing commands, and prints delimited sections. It does not rank or judge anything; that's your job, because judging safety requires reasoning the script can't do (e.g. "is this the currently active version," "is a process using this path right now").

## Phase 2: Turn raw data into a ranked, judged list

Walk through each section of the script output and build a candidate list, applying these safety rules as you go:

- **Cross-check against "RUNNING PROCESS PATHS" first.** Before listing anything as a candidate, check whether its path (or an ancestor directory) appears as a `pid=... exe=` or `pid=... cwd=` entry. If it does, that thing is **in use — never include it as a removable candidate**, regardless of what category it falls under. This is the rule that would have stopped a bad suggestion in practice: an actively-running binary or an actively-running dev server's `node_modules` must be excluded, not just deprioritized.
- **Never suggest touching `/swapfile`** (or any swap file) — the scan script already excludes it from the large-files section, but don't reintroduce it from another angle.
- **Version-manager dirs (Claude Code versions, nvm, asdf, etc.):** only the *older, inactive* entries are candidates. Determine "active" from evidence — nvm's `alias/default` + current `node --version`, asdf's `.tool-versions` references, or (for tools without an explicit pointer, like Claude Code's `versions/` dir) the highest version number *and* a check that no running process's `exe` points at an older one. Never flag the version matching what's currently running or aliased as default.
- **node_modules:** the script already flags directories as `idle` vs `POSSIBLY IN USE`. Only list `idle` ones as candidates; surface `POSSIBLY IN USE` ones as "skip — looks active" rather than silently omitting them (the user should know why it's not in the list).
- **Docker:** never propose a blind `docker system prune -a`. Break it into the same line items `docker system df` reports — images, build cache, volumes — as separate selectable options, so the user can keep e.g. volumes while clearing build cache. Only dangling/unused images and reclaimable build cache are safe defaults; images backing a running container (cross-reference the `docker ps -a` "Up" entries) must never be listed.
- **Caches (`~/.npm`, `~/.cache/*`, `~/.bun`, pip cache, etc.):** these regenerate on demand, so they're low-risk, but still show them as line items with sizes rather than one giant "clear all caches" blob — some may be much bigger than others and worth calling out individually (e.g. a browser-automation cache like Playwright's Chromium download vs. a small npm index).
- **Large individual files:** treat this section as a catch-all safety net, not a primary source — investigate anything that shows up before suggesting it, since an oversized file could be legitimate data.
- **Journal logs:** always safe to vacuum by time (e.g. keep last 7 days); frame the reclaim command with `--vacuum-time`, not `--vacuum-size=0` or deleting the journal directory directly.

For each surviving candidate, note: what it is, its size, one line on why it's safe (or the caveat if it's not fully risk-free), and the exact command that would reclaim it.

## Phase 3: Present the report, then let the user choose

First, show the headline numbers from the `DISK OVERVIEW` section (used/total/percent/free) as context.

Then present the candidates as prose or a table, **ranked biggest-reclaimable-first**, grouped by category. Do this as a plain report — do not execute anything yet.

Then use `AskUserQuestion` with `multiSelect: true` to let the user pick which categories/items to actually clean. Put the size in each option's label or description so the choice is informed, e.g.:

- "Docker build cache — 803M, fully regenerable"
- "Old Claude CLI versions (2.1.218, 2.1.219) — 530M, not the active version"
- "octo-stalker node_modules — 577M, idle (no running process)"

If there are more than 4 distinct candidates (AskUserQuestion caps at 4 options per question), group closely-related small items into one option (e.g. "misc package caches — npm+pip+bun, 310M total") rather than truncating the list, and mention in your prose report what got grouped.

## Phase 4: Execute only what was selected

For each selected item, run the specific, targeted command for that exact item — never a broader sweep than what was chosen:

- Use `/bin/rm -rf <exact-path>` (not bare `rm`) for filesystem deletions, so an interactive-confirmation shell alias doesn't silently hang the command. This does not change the safety bar — it's still one targeted path per command, confirmed by the user's selection, never a wildcard or directory the user didn't see itemized.
- Docker: `docker image prune` / `docker rmi <specific image>` / `docker builder prune -af` / `docker volume rm <specific volume>` — matching exactly the line item the user picked, not `docker system prune -a`.
- nvm: `nvm uninstall <version>`.
- asdf: `asdf uninstall <plugin> <version>`.
- Journal: `journalctl --vacuum-time=<N>d`.

Re-verify immediately before deleting anything long-lived between the scan and the delete (e.g. re-check `pgrep`/`lsof` for a node_modules directory) in case something started using it in the meantime.

## Phase 5: Report results

Show `df -h` before/after and the total space reclaimed, plus a one-line summary of what was removed per category. If something in the selection failed (e.g. Docker image still referenced by a container that started mid-session), say so explicitly rather than silently skipping it.
