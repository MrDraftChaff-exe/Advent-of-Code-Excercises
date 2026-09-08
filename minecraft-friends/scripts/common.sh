#!/usr/bin/env bash
# Shared paths and helpers. Source from other scripts in this directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/runtime"
CACHE="$ROOT/.cache"
TEMPLATES="$ROOT/templates"
VERSIONS_FILE="$ROOT/versions.conf"

load_versions() {
  # shellcheck disable=SC1090
  source "$VERSIONS_FILE"
  MC_VERSION="${MC_VERSION:-26.2}"
  MC_SERVER_SHA1="${MC_SERVER_SHA1:-}"
  MC_SERVER_URL="${MC_SERVER_URL:-}"
  JAVA_MAJOR="${JAVA_MAJOR:-25}"
  PLAYIT_TAG="${PLAYIT_TAG:-v1.0.10}"
  MC_MEMORY="${MC_MEMORY:-2G}"
  SERVER_PORT="${SERVER_PORT:-25565}"
}

ensure_dirs() {
  mkdir -p "$RUNTIME" "$CACHE" "$CACHE/bin"
}

java_bin() {
  if [[ -x "$CACHE/jdk/bin/java" ]]; then
    echo "$CACHE/jdk/bin/java"
    return
  fi
  if [[ -x "$CACHE/jdk/Contents/Home/bin/java" ]]; then
    echo "$CACHE/jdk/Contents/Home/bin/java"
    return
  fi
  if command -v java >/dev/null 2>&1; then
    command -v java
    return
  fi
  echo ""
}

java_major_version() {
  local bin="$1"
  "$bin" -version 2>&1 | python3 -c 'import sys,re
text=sys.stdin.read()
m=re.search(r"version \"([0-9]+)", text)
print(m.group(1) if m else "")'
}

require_java() {
  local bin
  bin="$(java_bin)"
  if [[ -z "$bin" ]]; then
    echo "Java ${JAVA_MAJOR}+ is not installed. Run: $ROOT/scripts/install.sh" >&2
    exit 1
  fi
  local major
  major="$(java_major_version "$bin")"
  if [[ -z "$major" || "$major" -lt "$JAVA_MAJOR" ]]; then
    echo "Java ${JAVA_MAJOR}+ is required for Minecraft ${MC_VERSION}. Found major=${major:-unknown}." >&2
    echo "Run: $ROOT/scripts/install.sh" >&2
    exit 1
  fi
  echo "$bin"
}

tmux_cmd() {
  if [[ -f /exec-daemon/tmux.portal.conf ]]; then
    echo tmux -f /exec-daemon/tmux.portal.conf
  else
    echo tmux
  fi
}

session_name() {
  echo "minecraft-server"
}

server_running() {
  local pidfile="$RUNTIME/server.pid"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  if command -v tmux >/dev/null 2>&1; then
    # shellcheck disable=SC2046
    $(tmux_cmd) has-session -t "$(session_name)" 2>/dev/null && return 0
  fi
  return 1
}

lan_ipv4() {
  python3 - <<'PY' 2>/dev/null || true
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
finally:
    s.close()
PY
}
