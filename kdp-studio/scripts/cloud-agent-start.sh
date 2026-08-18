#!/usr/bin/env bash
# Per-boot: keep Preview Studio listening on 8765.
# Must exist at the path configured in the Cloud Agent environment `start` command.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8765}"

if [[ ! -d "$ROOT/tools" ]]; then
  echo "kdp-studio/tools missing; nothing to start"
  exit 0
fi

if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "Preview Studio already up on :${PORT}"
  # Stay attached so Cloud Agent start phase has a long-lived process
  exec python3 - <<'PY'
import time
while True:
    time.sleep(3600)
PY
fi

cd "$ROOT/tools"
exec python3 -m kdp_studio preview --host 0.0.0.0 --port "$PORT"
