#!/usr/bin/env bash
# Start the vanilla dedicated server in the background.
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions
ensure_dirs

if server_running; then
  echo "Server is already running (pid $(cat "$RUNTIME/server.pid" 2>/dev/null || echo unknown))."
  echo "Join at localhost:${SERVER_PORT}  or  $(lan_ipv4):${SERVER_PORT}"
  exit 0
fi

if [[ ! -f "$RUNTIME/server.jar" ]]; then
  echo "Server is not installed yet."
  "$ROOT/scripts/install.sh"
fi

JAVA="$(require_java)"
cd "$RUNTIME"
: "${MC_MEMORY:=2G}"

SESSION="$(session_name)"
JAVA_ARGS=(-Xms1G -Xmx"${MC_MEMORY}" -jar server.jar nogui)

start_with_tmux() {
  local tmux_bin
  tmux_bin="$(tmux_cmd)"
  # shellcheck disable=SC2086
  $tmux_bin new-session -d -s "$SESSION" -c "$RUNTIME" -- "$JAVA" "${JAVA_ARGS[@]}"
  # Capture the pane pid.
  local pid
  pid="$($tmux_bin list-panes -t "$SESSION" -F '#{pane_pid}' | head -n 1)"
  echo "$pid" > "$RUNTIME/server.pid"
}

start_with_nohup() {
  nohup "$JAVA" "${JAVA_ARGS[@]}" > "$RUNTIME/server.console.log" 2>&1 &
  echo $! > "$RUNTIME/server.pid"
}

if command -v tmux >/dev/null 2>&1; then
  start_with_tmux
  echo "Started in tmux session '${SESSION}'. Attach with:  $(tmux_cmd) attach -t ${SESSION}"
else
  start_with_nohup
  echo "Started with nohup (pid $(cat "$RUNTIME/server.pid")). Logs: $RUNTIME/logs/latest.log"
fi

echo "Waiting for the world to finish loading (first boot can take a minute)..."
ready=0
for _ in $(seq 1 90); do
  if [[ -f "$RUNTIME/logs/latest.log" ]] && grep -Eq 'Done \(|For help, type "help"' "$RUNTIME/logs/latest.log"; then
    ready=1
    break
  fi
  if ! server_running; then
    echo "Server process exited before it became ready. Last log lines:" >&2
    tail -n 40 "$RUNTIME/logs/latest.log" 2>/dev/null || tail -n 40 "$RUNTIME/server.console.log" 2>/dev/null || true
    exit 1
  fi
  sleep 2
done

if [[ "$ready" -ne 1 ]]; then
  echo "Timed out waiting for the server. It may still be generating the world." >&2
  echo "Watch logs with:  tail -f $RUNTIME/logs/latest.log" >&2
  exit 1
fi

LAN="$(lan_ipv4)"
echo
echo "Server is up (Minecraft ${MC_VERSION})."
echo "  You:     localhost:${SERVER_PORT}"
if [[ -n "$LAN" ]]; then
  echo "  Same Wi-Fi friends:  ${LAN}:${SERVER_PORT}"
fi
echo "  Internet friends:    $ROOT/scripts/open-to-friends.sh"
echo
echo "In the Minecraft launcher, use the same version (${MC_VERSION}), then"
echo "Multiplayer → Direct Connection and paste one of the addresses above."
