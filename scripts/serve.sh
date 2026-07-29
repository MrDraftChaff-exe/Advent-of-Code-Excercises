#!/usr/bin/env bash
# Serve the exported Feather Hill Maine Coons site locally.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8080}"
cd "$ROOT/site"
echo "Serving Feather Hill Maine Coons at http://127.0.0.1:${PORT}/"
echo "Press Ctrl+C to stop."
exec python3 -m http.server "$PORT" --bind 127.0.0.1
