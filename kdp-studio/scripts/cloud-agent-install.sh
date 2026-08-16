#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$ROOT/requirements.txt" ]]; then
  echo "kdp-studio/requirements.txt not present; skipping install"
  exit 0
fi

python3 -m pip install --user -r "$ROOT/requirements.txt"
python3 -c 'import PIL, reportlab, pypdf; print("kdp-studio deps ok")'
