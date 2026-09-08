#!/usr/bin/env bash
# Ask the dedicated server to shut down cleanly.
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions
ensure_dirs

if ! server_running; then
  echo "Server is not running."
  rm -f "$RUNTIME/server.pid"
  exit 0
fi

SESSION="$(session_name)"
if command -v tmux >/dev/null 2>&1 && $(tmux_cmd) has-session -t "$SESSION" 2>/dev/null; then
  $(tmux_cmd) send-keys -t "$SESSION:0.0" "stop" C-m
else
  pid="$(cat "$RUNTIME/server.pid" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]]; then
    kill -TERM "$pid" 2>/dev/null || true
  fi
fi

for _ in $(seq 1 30); do
  if ! server_running; then
    rm -f "$RUNTIME/server.pid"
    echo "Server stopped."
    exit 0
  fi
  sleep 1
done

echo "Server did not stop in time; sending SIGKILL." >&2
pid="$(cat "$RUNTIME/server.pid" 2>/dev/null || true)"
if [[ -n "${pid:-}" ]]; then
  kill -KILL "$pid" 2>/dev/null || true
fi
if command -v tmux >/dev/null 2>&1; then
  $(tmux_cmd) kill-session -t "$SESSION" 2>/dev/null || true
fi
rm -f "$RUNTIME/server.pid"
echo "Server killed."
