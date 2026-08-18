#!/usr/bin/env bash
# One-command KDP upload kit for Buildings (buildings-40).
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="buildings-40"
TOOLS="$ROOT/tools"
KIT="$ROOT/products/$SLUG/upload-kit"

cd "$TOOLS"
echo "==> Stage upload kit for $SLUG"
python3 - <<PY
from kdp_studio.publish import stage_upload_kit
import json
result = stage_upload_kit("$SLUG")
print(json.dumps({k: result.get(k) for k in ("ok", "kit_dir", "files", "errors")}, indent=2, default=str))
if not result.get("ok"):
    raise SystemExit(1)
PY

echo
echo "Upload kit ready:"
ls -lh "$KIT"
echo
echo "Quick start:  $KIT/00-UPLOAD-NOW.md"
echo "Paste fields: $KIT/paste-fields/"
echo "Bookshelf:    https://kdp.amazon.com/en_US/bookshelf"
echo
echo "Or open Preview Studio → select Buildings → Publish → Stage upload kit"
