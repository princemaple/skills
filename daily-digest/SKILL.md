---
name: daily-digest
description: "Scans all git repos under a folder (default ~/code) for commits in a recent time window and writes a plain-language Chinese summary of what changed, aimed at someone who wants a quick 'what happened while I was away' briefing rather than a technical changelog. Use whenever the user asks what's changed recently, wants a daily/weekly digest of commits across their repos, asks 'what did I ship yesterday', wants a status update to share with non-engineers, or wants to know what to spot-check after a batch of commits landed. Trigger phrases: 'daily digest', '今天有什么更新', 'what changed today/this week', 'summarize recent commits', 'catch me up on the repos'."
---

# Daily Digest

Turn raw git history across multiple repos into a short, non-technical Chinese
briefing: what changed, and what's worth double-checking. The reader is
assumed to *not* want to parse commit messages or diffs themselves — that's
the whole point of this skill.

## Workflow

### 1. Figure out scope and time window

- Repo root: default to `~/code`. If the user names specific repos, skip
  discovery and use those paths directly.
- Time window: default to the past 24 hours. If the user gives a duration or
  date (e.g. "3 days", "since Monday", "上周", "since 2026-07-01"), convert it
  to something `git log --since` understands — git accepts most natural
  phrasing directly (`"3 days ago"`, `"2026-07-01"`, `"monday"`), so light
  normalization is usually enough. When in doubt, err toward a slightly wider
  window rather than missing commits.

### 2. Discover repos

```bash
bash <skill-path>/scripts/find_repos.sh ~/code
```

This finds every git repo up to 3 levels deep. Skip any repo the scan turns
up empty for the window — don't mention it in the output.

### 3. Pull commits per repo

For each repo, in parallel:

```bash
bash <skill-path>/scripts/scan_commits.sh <repo_path> "<since>"
```

This dumps commits on the currently checked-out branch (usually the default
branch — that's deliberate, since the goal is "what landed," not every
feature-branch WIP commit) with subject, full body, and changed-file list,
delimited by `@@COMMIT@@` / `@@FILES@@` / `@@END@@` markers.

### 4. Classify each commit

For every commit, decide which bucket it falls into. Read the subject/body
first — only fall back to inspecting code when the message itself can't tell
you what changed.

**a. Dependency-only — drop entirely.**
The changed-file list is *only* lockfiles/manifests (`package.json`,
`bun.lock`, `bun.lockb`, `yarn.lock`, `pnpm-lock.yaml`, `Gemfile.lock`,
`mix.lock`, `go.mod`, `go.sum`, `Cargo.lock`, `requirements.txt`,
`poetry.lock`), or the subject is an obvious bump (`bumps`, `chore(deps):
bump x`, `upgrade deps`). Don't narrate these at all — just tally a count for
the footer.

**b. Non-user-facing — skip from the narrative, but keep for the warning list.**
Subject matches conventional no-behavior-change types (`refactor:`,
`chore:`, `test:`, `ci:`, `docs:`, `style:`, or bare words like `format`,
`格式化`, `整理代码`) *and* nothing in the message suggests a user-visible
side effect. Don't describe these as features, but do keep their touched
files — a "pure refactor" can still introduce a regression, and that risk is
exactly what the warning section is for.

**c. Good message — summarize directly.**
The subject (+ body, if present) clearly explains what changed and why in
plain terms. This is the common case for well-written commits — use the
message as your source, don't go re-deriving it from the diff.

**d. Bad message — go look at the code.**
The subject is vague or unhelpful on its own (`fix`, `fix bug`, `update`,
`wip`, `misc changes`, `调整`, a subject with no body that doesn't explain
*what* or *why*). Only for these, run:

```bash
git -C <repo_path> show --stat <hash>
git -C <repo_path> diff <hash>^..<hash> -- <relevant files>
```

to figure out what actually happened, then summarize that in plain language.
Don't do this for every commit — it's expensive and unnecessary when the
message already does the job.

### 5. Write the summary

Audience is non-technical. That means:
- No jargon: don't say "refactor", "hook", "endpoint", "PR", "interceptor",
  "组件", "重构" etc. Describe what the *user of the product* would notice
  ("现在批量操作失败时,只有失败的那几项需要重试" not "batch update now uses
  catchError with 5 concurrent isolation").
  - It's fine to keep the intent even if you drop the mechanism — describe
    the improvement/fix in terms of what the app now does differently.
- Group related commits together into one bullet rather than listing every
  commit 1:1 — a feature that landed across 3 commits should read as one
  item.
- Keep it short. This is a briefing, not a changelog.

For the warning section, group touched files by their top-level directory
(e.g. `projects/works`, `projects/plan`, `lib/app/accounts`) and
describe in guidance language what to spot-check — don't just list file
paths. Include areas touched by skipped refactor/internal commits too, since
those are exactly the kind of change that silently breaks something without
announcing it in the commit message.

### 6. Output format

Use this structure (adapt headers/wording, but keep the shape) — write the
whole thing in **简体中文**:

```markdown
# 每日更新摘要
时间范围：过去 24 小时（或用户指定的范围）

## 总览
一两句话总结这段时间大致做了什么。

## 仓库：<repo 中文/易懂描述>
### 这次更新了什么
- 用大白话描述的变更点，按功能分组，不是逐条 commit 翻译

### 需要留意的地方
- 涉及模块：xxx —— 建议实际用一下 xxx 功能，确认没有问题
- （只有在有理由怀疑风险时才写，没有就省略这个小节或写"这次改动风险较低"）

（如果扫描了多个仓库，每个仓库重复上面两个小节；仓库之间用 --- 分隔）

---
另有 N 项依赖更新、M 项代码整理，未在上面详细列出。
```

Repos with zero in-scope commits (everything filtered as dependency/internal,
or no commits at all) get a one-line mention at most, not a full section.

### 7. Deliver both a chat reply and an artifact

Per how this skill is normally used: give the user the summary directly in
the conversation, *and* render the same content as a Markdown/HTML artifact
(via the Artifact tool) so it's easy to share or revisit. Keep them in sync —
same content, the artifact just gets nicer formatting.
