#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pip install -r requirements.txt -q
cd tools
SLUG="${1:-forest-animals-30}"
if [[ ! -f "../products/$SLUG/meta.json" ]]; then
  python3 -m kdp_studio new --slug "$SLUG" --title "Forest Animals" --subtitle "30 Woodland Friends to Color" --designs 30
fi
python3 -m kdp_studio pages --slug "$SLUG"
python3 -m kdp_studio interior --slug "$SLUG"
python3 -m kdp_studio cover --slug "$SLUG" --render
python3 -m kdp_studio validate --slug "$SLUG"
echo "Done: products/$SLUG"
