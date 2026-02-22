#!/usr/bin/env bash
# fetch-docker-versions.sh
# Fetches the latest Debian bookworm date tag and Alpine version from Docker Hub.
#
# Usage:
#   ./fetch-docker-versions.sh          # prints both
#   ./fetch-docker-versions.sh debian   # prints only: bookworm-YYYYMMDD-slim
#   ./fetch-docker-versions.sh alpine   # prints only: X.Y.Z

set -euo pipefail

DEBIAN_API="https://hub.docker.com/v2/repositories/library/debian/tags?name=bookworm-&ordering=last_updated&page_size=20"
ALPINE_API="https://hub.docker.com/v2/repositories/library/alpine/tags?ordering=last_updated&page_size=20"

# Extract .results[].name from Docker Hub API JSON.
# Tries jq first (fastest), then python3, then a grep fallback.
extract_names() {
  local json="$1"
  if command -v jq &>/dev/null; then
    echo "$json" | jq -r '.results[].name'
  elif command -v python3 &>/dev/null; then
    echo "$json" | python3 -c "
import sys, json
for r in json.load(sys.stdin).get('results', []):
    print(r['name'])
"
  else
    # Portable grep fallback (no -P needed)
    echo "$json" | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//'
  fi
}

fetch_latest_debian_date() {
  local json
  json=$(curl -sf "$DEBIAN_API")
  extract_names "$json" \
    | grep -E '^bookworm-[0-9]{8}-slim$' \
    | grep -oE '[0-9]{8}' \
    | sort -r \
    | head -1
}

fetch_latest_alpine_version() {
  local json
  json=$(curl -sf "$ALPINE_API")
  extract_names "$json" \
    | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' \
    | sort -t. -k1,1n -k2,2n -k3,3n \
    | tail -1
}

MODE="${1:-all}"

case "$MODE" in
  debian)
    DATE=$(fetch_latest_debian_date)
    if [ -z "$DATE" ]; then
      echo "ERROR: could not determine latest Debian bookworm date" >&2
      exit 1
    fi
    echo "bookworm-${DATE}-slim"
    ;;

  alpine)
    VERSION=$(fetch_latest_alpine_version)
    if [ -z "$VERSION" ]; then
      echo "ERROR: could not determine latest Alpine version" >&2
      exit 1
    fi
    echo "$VERSION"
    ;;

  all)
    DATE=$(fetch_latest_debian_date)
    VERSION=$(fetch_latest_alpine_version)
    echo "debian: bookworm-${DATE}-slim"
    echo "alpine: ${VERSION}"
    ;;

  *)
    echo "Usage: $0 [debian|alpine|all]" >&2
    exit 1
    ;;
esac
