#!/usr/bin/env bash
# Per-boot: start Preview Studio on :8765, then return.
# Cloud Agent `start` (and the Save form) hang if this process never exits.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
USER_SITE="$(python3 -c 'import site; print(site.getusersitepackages())')"
export PYTHONPATH="${USER_SITE}${PYTHONPATH:+:${PYTHONPATH}}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8765}"
LOG="${TMPDIR:-/tmp}/kdp-preview.log"

if [[ ! -d "$ROOT/tools" ]]; then
  echo "kdp-studio/tools missing; nothing to start"
  exit 0
fi

if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "Preview Studio already up on :${PORT}"
  exit 0
fi

cd "$ROOT/tools"
nohup python3 -m kdp_studio preview --host 0.0.0.0 --port "$PORT" >>"$LOG" 2>&1 &
disown || true

for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    echo "Preview Studio listening on :${PORT}"
    exit 0
  fi
  sleep 0.25
done

echo "Preview Studio did not become ready; see ${LOG}" >&2
exit 0
