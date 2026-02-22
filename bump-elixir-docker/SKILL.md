---
name: bump-elixir-docker
description: Bumps Elixir Dockerfile versions to latest tags from Docker Hub. Use when updating Dockerfile, bumping Elixir versions, upgrading Docker images, or modernizing container builds for Elixir projects.
allowed-tools: Read, Edit, Bash, WebFetch
---

# Bump Elixir Docker Images

This skill updates Elixir project Dockerfiles to use the latest available Docker images from Docker Hub for both the Elixir builder stages and the final runtime stage.

## Workflow

### 1. Read and Analyze the Dockerfile

Read the Dockerfile and identify:
- Whether it uses **Debian** or **Alpine** base images
- Current Elixir version (e.g., `1.19.4`)
- Current Erlang version (e.g., `28.2`)
- Current OS version tags
- All `FROM` statements that need updating

**Detection patterns:**
- Debian: `hexpm/elixir:*-debian-*` or final stage `FROM debian:*`
- Alpine: `hexpm/elixir:*-alpine-*` or final stage `FROM alpine:*`

### 2. Find Latest OS Date/Version FIRST

Use the **Docker Hub API via WebFetch** to find the latest OS date (Debian) or version (Alpine). Do not guess or probe dates — fetch the real tag list.

**Why first?** Different OS dates/versions may have different Elixir/Erlang versions available.

### 3. Probe for Newer Elixir/Erlang Versions

Using the NEW OS date/version from step 2, incrementally probe for newer Elixir/Erlang versions using `docker manifest inspect`.

### 4. Find Latest Base OS Image

The base OS date/version was already retrieved in Step 2 via Docker Hub API — reuse that result. No separate probing needed.

### 5. Verify Complete Image Tags Exist

**CRITICAL**: Before updating any files, verify both the Elixir builder image and base OS image exist using `docker manifest inspect`.

### 6. Update the Dockerfile

Only after verification, use Edit tool to update all FROM statements.

## Find Latest Versions Using Incremental Probing

**CRITICAL**: The hexpm/elixir repository has too many tags to efficiently search. Use **incremental version probing** instead of parsing the entire tag list.

#### Strategy: Probe for Newer Versions

**CRITICAL ORDER**: Must find the latest OS date/version FIRST, then probe Elixir/Erlang with that new OS version.

**Step 1: Find Latest OS Date/Version First**

Before probing Elixir/Erlang versions, find the latest OS date or version by **fetching the Docker Hub API**. Never guess or manually probe dates.

Run the helper script bundled with this skill — it queries the Docker Hub API and returns a single, unambiguous answer:

```bash
# For Debian — outputs e.g. "bookworm-20260202-slim"
bash ~/.claude/skills/bump-elixir-docker/fetch-docker-versions.sh debian

# For Alpine — outputs e.g. "3.21.3"
bash ~/.claude/skills/bump-elixir-docker/fetch-docker-versions.sh alpine

# Both at once
bash ~/.claude/skills/bump-elixir-docker/fetch-docker-versions.sh
```

The script fetches the Docker Hub tags API, filters for the right pattern (`bookworm-YYYYMMDD-slim` or `X.Y.Z`), and returns the newest value. It requires `curl` and one of `jq`, `python3`, or `grep` (all typically available).

**Step 2: Probe for Newer Elixir/Erlang with NEW OS Version**

Now test for newer Elixir/Erlang versions using the **latest OS date/version found in Step 1**:

1. **Test Elixir patch bumps** (1.19.5, 1.19.6, etc.) - keep Erlang same, use new OS
2. **Test Elixir minor bumps** (1.20.0, 1.20.1, etc.) - keep Erlang same, use new OS
3. **Test Erlang patch bumps** (28.2.1, 28.2.2, etc.) - keep Elixir same, use new OS
4. **Test Erlang minor bumps** (28.3, 28.4, etc.) - keep Elixir same, use new OS
5. **Test Erlang major bumps** (29.0, 29.1, etc.) - keep Elixir same, use new OS

Use `docker manifest inspect` to test if a tag exists (fast and reliable):
```bash
# Example: Testing with NEW OS date (20251229), not old date
docker manifest inspect hexpm/elixir:1.19.5-erlang-28.2-debian-bookworm-20251229-slim
```
- Success: Tag exists, continue testing higher versions
- Error "no such manifest": Tag doesn't exist, stop probing that version series

**Example probing loop for Elixir patches:**
```bash
# Use the NEW date found in Step 1
NEW_DATE="20251229"
for patch in 5 6 7 8 9; do
  docker manifest inspect hexpm/elixir:1.19.$patch-erlang-28.2-debian-bookworm-$NEW_DATE-slim >/dev/null 2>&1 && echo "EXISTS" || echo "not found"
done
```

**Short-circuit optimization:**
If a lower version doesn't exist (e.g., 1.19.5), higher versions likely don't either (1.19.6, 1.19.7) - skip to the next series (e.g., 1.20.x).

**Step 3: Find Latest Base OS Image**

The latest base OS date/version was already retrieved in Step 1 via the Docker Hub API — reuse that result. No additional probing needed for the base image tag.

**CRITICAL VERSION CONSTRAINT:**
- **NEVER downgrade Elixir or Erlang versions**
- Only select a new version if `new_elixir >= current_elixir` AND `new_erlang >= current_erlang`
- If no newer version exists, keep the current version and only update OS date/version
- Compare versions using semantic versioning rules (1.20.0 > 1.19.4, 28.2 > 27.3)

#### Verify Final Image Combination Exists

**CRITICAL**: After finding the latest versions, verify the complete tag exists before updating the Dockerfile.

Use `docker manifest inspect` to verify:
```bash
# For Debian
docker manifest inspect hexpm/elixir:1.19.4-erlang-28.2-debian-bookworm-20251229-slim

# For Alpine
docker manifest inspect hexpm/elixir:1.19.4-erlang-28.3-alpine-3.23.2
```

Also verify the base OS image exists:
```bash
# For Debian
docker manifest inspect debian:bookworm-20251229-slim

# For Alpine
docker manifest inspect alpine:3.23.2
```

If either image doesn't exist:
- Fall back to the previous known working version
- Try the next-lower OS version (e.g., if 20251229 fails, try 20251208)
- Report to user which combination was found vs. which was attempted

## Update the Dockerfile

Use the Edit tool to update **ALL** `FROM` statements:

**For Debian projects:**
- Update all `FROM hexpm/elixir:*-debian-*` lines with new Elixir/Erlang/date
- Update `FROM debian:*` line with new date tag
- Ensure version consistency across all builder stages (deps, dev, release)

**For Alpine projects:**
- Update all `FROM hexpm/elixir:*-alpine-*` lines with new Elixir/Erlang/Alpine version
- Update `FROM alpine:*` line with new Alpine version
- Ensure version consistency across all builder stages

**Example edits:**

Debian (version bump):
```dockerfile
# Old
FROM hexpm/elixir:1.19.4-erlang-28.2-debian-bookworm-20251117-slim AS deps

# New (Elixir and Erlang bumped)
FROM hexpm/elixir:1.20.1-erlang-29.0-debian-bookworm-20260115-slim AS deps
```

Debian (only OS date updated, versions unchanged):
```dockerfile
# Old
FROM hexpm/elixir:1.19.4-erlang-28.2-debian-bookworm-20251117-slim AS deps

# New (only date bumped, Elixir/Erlang unchanged)
FROM hexpm/elixir:1.19.4-erlang-28.2-debian-bookworm-20260115-slim AS deps
```

Alpine:
```dockerfile
# Old
FROM hexpm/elixir:1.19.4-erlang-28.2-alpine-3.22.2 AS deps

# New
FROM hexpm/elixir:1.20.1-erlang-29.0-alpine-3.23.0 AS deps
```

**If no upgrade is available:**
- Still update the OS base date/version if newer exists
- Keep Elixir and Erlang versions unchanged
- Report to user that current versions are already latest

## Report Changes

After updating, provide a summary:
- Old Elixir version → New Elixir version (or "unchanged")
- Old Erlang version → New Erlang version (or "unchanged")
- Old OS version → New OS version
- Number of `FROM` statements updated
- Whether this was a version upgrade or just OS update
- Recommendation to test the build

## Important Notes

1. **CRITICAL WORKFLOW ORDER**: Find latest OS date/version FIRST (via Docker Hub API), then probe Elixir/Erlang with that new OS. Different OS dates have different Elixir/Erlang versions available!
2. **Never downgrade**: CRITICAL - Never select Elixir or Erlang versions lower than current
3. **Always verify images exist**: Use `docker manifest inspect` to verify both builder and base images exist BEFORE updating Dockerfile
4. **Version consistency**: All builder stages (deps, dev, release) must use the SAME Elixir image tag
5. **OS matching**: The final stage OS must match the builder stage OS flavor (Debian with Debian, Alpine with Alpine)
6. **Slim variants**: Prefer `-slim` variants for Debian to reduce image size
7. **Probe limits**: Keep probe sets small; stop once newer versions are not found in a series
8. **Semantic versioning**: When comparing versions, use proper semantic version sorting (1.20.1 > 1.19.4, 28.2 > 27.3)
9. **Testing**: Always recommend running `docker build` to verify the new images work
10. **OS updates are safe**: Even if Elixir/Erlang can't be bumped, updating Debian date or Alpine version is beneficial
11. **Short-circuit probing**: If a lower version doesn't exist, higher versions likely don't either - stop probing

## Example Usage

**User says:**
- "Bump the Dockerfile"
- "Update Elixir version in Docker"
- "Upgrade Docker images to latest"
- "Check for newer Elixir image tags"

**Skill activates and:**
1. Reads Dockerfile
2. Detects it's Alpine-based with Elixir 1.19.4, Erlang 28.2, Alpine 3.22.2
3. **Finds latest OS version first**: Queries Docker Hub API for tags matching "1.19.4-erlang-28.2-alpine"
4. Discovers Alpine 3.23.2 is available (old was 3.22.2)
5. **Probes for newer Elixir/Erlang with NEW Alpine version (3.23.2)**:
   - Tests Elixir 1.19.5 with Alpine 3.23.2 - not found
   - Tests Elixir 1.20.0 with Alpine 3.23.2 - not found
   - Tests Erlang 28.3 with Alpine 3.23.2 - **EXISTS!**
   - Tests Erlang 28.4 with Alpine 3.23.2 - not found, 28.3 is latest
6. Queries for latest Alpine base image - confirms alpine:3.23.2
7. **Verifies images exist**:
   - `docker manifest inspect hexpm/elixir:1.19.4-erlang-28.3-alpine-3.23.2` ✅
   - `docker manifest inspect alpine:3.23.2` ✅
8. Updates all 4 FROM statements
9. Reports: Elixir unchanged, Erlang 28.2→28.3, Alpine 3.22.2→3.23.2

## Script and Manifest Inspect Examples

### Find Latest Debian Date or Alpine Version (Script)
```bash
# Returns e.g. "bookworm-20260202-slim"
bash ~/.claude/skills/bump-elixir-docker/fetch-docker-versions.sh debian

# Returns e.g. "3.21.3"
bash ~/.claude/skills/bump-elixir-docker/fetch-docker-versions.sh alpine
```

### Probe for specific Elixir+Erlang combo (Debian)
```bash
docker manifest inspect hexpm/elixir:1.19.5-erlang-28.3.1-debian-bookworm-20260202-slim
```

### Probe for specific Elixir+Erlang combo (Alpine)
```bash
docker manifest inspect hexpm/elixir:1.19.5-erlang-28.3.1-alpine-3.23.2
```

## Troubleshooting

- **No tags found**: Increase `page_size` or check the filter string
- **No upgrade available**: Report current versions are latest, but still update OS date/version
- **Version parsing fails**: Handle edge cases like rc/beta versions
- **No tag found**: Reduce the probe set and keep the current version/date
- **Incompatible versions**: Skip tags that would downgrade Elixir or Erlang
- **Major version bump**: Warn user if major Elixir or Erlang version increases (e.g., 1.x → 2.x)
- **Different Elixir/Erlang versions available for Debian vs Alpine**: This is normal - probe with the NEW OS date/version, not the old one. Different OS dates may have different Elixir/Erlang versions available.
- **Missed newer Erlang version**: You likely probed with the old OS date instead of the new one. Always find OS date FIRST, then probe Elixir/Erlang.
