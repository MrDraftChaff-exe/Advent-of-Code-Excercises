#!/usr/bin/env bash
# Send a command to the running Minecraft console (for example: op Steve).
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <minecraft console command>" >&2
  echo "Example: $0 'op Steve'" >&2
  exit 1
fi

if ! server_running; then
  echo "Server is not running." >&2
  exit 1
fi

SESSION="$(session_name)"
if ! command -v tmux >/dev/null 2>&1 || ! $(tmux_cmd) has-session -t "$SESSION" 2>/dev/null; then
  echo "Console commands need the server started via tmux (./scripts/start-server.sh)." >&2
  exit 1
fi

$(tmux_cmd) send-keys -t "$SESSION:0.0" "$*" C-m
echo "Sent: $*"
