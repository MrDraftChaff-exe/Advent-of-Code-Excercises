#!/usr/bin/env bash
# Print whether the dedicated server is up, and ping the Minecraft protocol.
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions
ensure_dirs

if server_running; then
  echo "process: running (pid $(cat "$RUNTIME/server.pid" 2>/dev/null || echo unknown))"
else
  echo "process: stopped"
fi

python3 "$ROOT/scripts/ping-server.py" "127.0.0.1" "${SERVER_PORT}"
LAN="$(lan_ipv4)"
if [[ -n "$LAN" ]]; then
  echo "lan-address: ${LAN}:${SERVER_PORT}"
fi
echo "local-address: localhost:${SERVER_PORT}"
