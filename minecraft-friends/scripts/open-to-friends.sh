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
LOG="$RUNTIME/playit.log"
SESSION="minecraft-playit"

if command -v tmux >/dev/null 2>&1 && $(tmux_cmd) has-session -t "$SESSION" 2>/dev/null; then
  echo "playit is already running in tmux session '${SESSION}'."
else
  rm -f "$LOG"
  PLAYIT_ARGS=(--secret-path "$SECRET" --log-path "$LOG")
  if command -v tmux >/dev/null 2>&1; then
    $(tmux_cmd) new-session -d -s "$SESSION" -- "$PLAYIT" "${PLAYIT_ARGS[@]}"
  else
    nohup "$PLAYIT" "${PLAYIT_ARGS[@]}" >/dev/null 2>&1 &
  fi
fi

echo "Waiting for a playit claim URL..."
claim=""
for _ in $(seq 1 30); do
  if [[ -f "$LOG" ]]; then
    claim="$(grep -Eo 'https://playit\.gg/claim/[A-Za-z0-9_-]+' "$LOG" | tail -n 1 || true)"
    if [[ -n "$claim" ]]; then
      break
    fi
  fi
  sleep 1
done

LAN="$(lan_ipv4)"
echo
echo "Local / same Wi-Fi (no tunnel needed):"
echo "  localhost:${SERVER_PORT}"
if [[ -n "$LAN" ]]; then
  echo "  ${LAN}:${SERVER_PORT}"
fi
echo
if [[ -n "$claim" ]]; then
  echo "Internet friends — finish the tunnel (one-time):"
  echo "  1. Open  $claim"
  echo "  2. Sign in (or create a free playit.gg account) and claim this agent."
  echo "  3. Add Tunnel → Minecraft Java → local address 127.0.0.1 port ${SERVER_PORT}."
  echo "  4. Copy the public address playit shows and send that to friends."
else
  echo "playit started, but no claim URL appeared yet. Check $LOG"
  echo "or run:  $PLAYIT_CLI claim generate"
fi
echo
echo "Friends must use Minecraft Java ${MC_VERSION} (same version as this server)."
echo "After they have joined once, lock it down with:"
echo "  $ROOT/scripts/console.sh whitelist add TheirName"
echo "  $ROOT/scripts/console.sh whitelist on"
