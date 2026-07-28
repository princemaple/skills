#!/usr/bin/env bash
# Read-only disk usage survey. Never deletes anything. Prints raw sections;
# the caller (Claude, via SKILL.md) is responsible for ranking, judging
# safety, and presenting a final list to the user.
set -uo pipefail

section() { printf '\n=== %s ===\n' "$1"; }

section "DISK OVERVIEW"
df -h 2>/dev/null | grep -v -E '^(tmpfs|overlay|udev)'

section "RUNNING PROCESS PATHS (do not suggest deleting these)"
for pid in /proc/[0-9]*; do
  p="${pid#/proc/}"
  exe=$(readlink -f "$pid/exe" 2>/dev/null)
  cwd=$(readlink -f "$pid/cwd" 2>/dev/null)
  [ -n "$exe" ] && echo "pid=$p exe=$exe"
  [ -n "$cwd" ] && echo "pid=$p cwd=$cwd"
done 2>/dev/null | sort -u -k2

section "DOCKER"
if command -v docker >/dev/null 2>&1; then
  echo "--- docker system df ---"
  docker system df 2>/dev/null
  echo "--- docker images (all) ---"
  docker images --format "{{.ID}}  {{.Repository}}:{{.Tag}}  {{.Size}}" 2>/dev/null
  echo "--- dangling images ---"
  docker images --filter "dangling=true" --format "{{.ID}}  {{.Size}}" 2>/dev/null
  echo "--- containers (running use their image; stopped containers are safe to consider) ---"
  docker ps -a --format "{{.ID}}  {{.Status}}  {{.Image}}  {{.Names}}" 2>/dev/null
  echo "--- volumes ---"
  docker volume ls --format "{{.Name}}" 2>/dev/null
else
  echo "docker not installed"
fi

section "VERSION-MANAGER DIRS (generic ~/.local/share/*/versions pattern, e.g. Claude Code)"
for d in "$HOME"/.local/share/*/versions; do
  [ -d "$d" ] || continue
  echo "-- $d --"
  ls -la "$d" 2>/dev/null | awk 'NR>1{print $NF, $5}'
  for f in "$d"/*; do
    [ -e "$f" ] || continue
    du -sh "$f" 2>/dev/null
  done
done

section "NVM"
if [ -d "$HOME/.nvm" ]; then
  echo "default alias: $(cat "$HOME/.nvm/alias/default" 2>/dev/null)"
  echo "currently active node: $(command -v node >/dev/null 2>&1 && node --version)"
  echo "installed versions:"
  du -sh "$HOME"/.nvm/versions/node/*/ 2>/dev/null
else
  echo "nvm not present"
fi

section "ASDF"
if [ -d "$HOME/.asdf" ]; then
  echo "installed versions:"
  for plugin_dir in "$HOME"/.asdf/installs/*/; do
    [ -d "$plugin_dir" ] || continue
    plugin=$(basename "$plugin_dir")
    for ver_dir in "$plugin_dir"*/; do
      [ -d "$ver_dir" ] || continue
      ver=$(basename "$ver_dir")
      size=$(du -sh "$ver_dir" 2>/dev/null | cut -f1)
      echo "$plugin $ver $size"
    done
  done
  echo "referenced versions (.tool-versions files found under \$HOME, depth 3):"
  find "$HOME" -maxdepth 3 -name ".tool-versions" -exec sh -c 'echo "-- $1 --"; cat "$1"' _ {} \; 2>/dev/null
else
  echo "asdf not present"
fi

section "PACKAGE MANAGER / TOOL CACHES"
for c in "$HOME/.npm" "$HOME/.cache/pip" "$HOME/.bun/install/cache" "$HOME/.cache"/*; do
  [ -e "$c" ] || continue
  du -sh "$c" 2>/dev/null
done | sort -rh -k1 | uniq

section "SYSTEMD JOURNAL"
if command -v journalctl >/dev/null 2>&1; then
  journalctl --disk-usage 2>/dev/null
else
  echo "journalctl not available"
fi

section "NODE_MODULES UNDER COMMON CODE ROOTS"
for root in "$HOME/code" "$HOME/projects" "$HOME/src" "$HOME/dev"; do
  [ -d "$root" ] || continue
  find "$root" -maxdepth 4 -type d -name node_modules -prune -print 2>/dev/null | while read -r nm; do
    size=$(du -sh "$nm" 2>/dev/null | cut -f1)
    proj_dir=$(dirname "$nm")
    proj_name=$(basename "$proj_dir")
    in_use="idle"
    if pgrep -f "$proj_dir" >/dev/null 2>&1; then
      in_use="POSSIBLY IN USE (matching process found)"
    fi
    if command -v lsof >/dev/null 2>&1 && lsof +D "$proj_dir" >/dev/null 2>&1; then
      in_use="POSSIBLY IN USE (open file handles)"
    fi
    echo "$nm  size=$size  project=$proj_name  status=$in_use"
  done
done

section "LARGE INDIVIDUAL FILES (>200M, excludes swapfile and docker overlay internals)"
find / -xdev -type f -size +200M \
  -not -path "/swapfile" \
  -not -path "/var/lib/docker/*" \
  -not -path "/proc/*" \
  2>/dev/null | while read -r f; do
  du -h "$f" 2>/dev/null
done | sort -rh
