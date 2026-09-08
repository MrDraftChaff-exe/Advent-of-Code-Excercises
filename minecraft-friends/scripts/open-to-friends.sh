#!/usr/bin/env bash
# Start the local server (if needed) and a playit.gg tunnel so friends
# outside your Wi-Fi can join without port forwarding.
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions
ensure_dirs

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This tunnel helper is wired for Linux. On macOS or Windows, start the"
  echo "server with start-server, then install playit from https://playit.gg/download"
  echo "and create a Minecraft Java tunnel to 127.0.0.1:${SERVER_PORT}."
  "$ROOT/scripts/start-server.sh"
  exit 0
fi

if [[ ! -x "$CACHE/bin/playit" ]]; then
  "$ROOT/scripts/install.sh"
fi

"$ROOT/scripts/start-server.sh"

PLAYIT="$CACHE/bin/playit"
PLAYIT_CLI="$CACHE/bin/playit-cli"
SECRET="$RUNTIME/playit.secret"
SOCKET="$RUNTIME/playit.sock"
LOG="$RUNTIME/playit.log"
SESSION="minecraft-playit"

playit_running() {
  command -v tmux >/dev/null 2>&1 && $(tmux_cmd) has-session -t "$SESSION" 2>/dev/null
}

if playit_running; then
  echo "playit is already running in tmux session '${SESSION}'."
else
  rm -f "$SOCKET"
  PLAYIT_ARGS=(
    --secret-path "$SECRET"
    --socket-path "$SOCKET"
    --log-path "$LOG"
  )
  $(tmux_cmd) new-session -d -s "$SESSION" -- "$PLAYIT" "${PLAYIT_ARGS[@]}"
  # Wait until the daemon is listening on the IPC socket.
  for _ in $(seq 1 20); do
    if "$PLAYIT_CLI" --socket-path "$SOCKET" status >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

CODE="$("$PLAYIT_CLI" --socket-path "$SOCKET" claim generate)"
CLAIM_URL="$("$PLAYIT_CLI" claim url --name minecraft-friends "$CODE")"

# Keep exchanging in the background so the secret lands once you claim in the browser.
EXCHANGE_SESSION="minecraft-playit-claim"
if command -v tmux >/dev/null 2>&1 && ! $(tmux_cmd) has-session -t "$EXCHANGE_SESSION" 2>/dev/null; then
  $(tmux_cmd) new-session -d -s "$EXCHANGE_SESSION" -- \
    "$PLAYIT_CLI" --socket-path "$SOCKET" claim exchange --wait 0 "$CODE"
fi

LAN="$(lan_ipv4)"
echo
echo "Local / same Wi-Fi (no tunnel needed):"
echo "  localhost:${SERVER_PORT}"
if [[ -n "$LAN" ]]; then
  echo "  ${LAN}:${SERVER_PORT}"
fi
echo
echo "Internet friends — finish the tunnel (one-time):"
echo "  1. Open  $CLAIM_URL"
echo "  2. Sign in (or create a free playit.gg account) and claim this agent."
echo "  3. Add Tunnel → Minecraft Java → local address 127.0.0.1 port ${SERVER_PORT}."
echo "  4. Copy the public address playit shows and send that to friends."
echo
echo "Friends must use Minecraft Java ${MC_VERSION} (same version as this server)."
echo "After they have joined once, lock it down with:"
echo "  $ROOT/scripts/console.sh whitelist add TheirName"
echo "  $ROOT/scripts/console.sh whitelist on"
