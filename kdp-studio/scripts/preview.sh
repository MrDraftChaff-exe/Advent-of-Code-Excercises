#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pip install -r requirements.txt -q
cd tools
exec python3 -m kdp_studio preview --host 0.0.0.0 --port "${PORT:-8765}"
