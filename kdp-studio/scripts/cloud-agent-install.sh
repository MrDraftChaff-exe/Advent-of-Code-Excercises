#!/usr/bin/env bash
# Idempotent Cloud Agent install for KDP Studio (Preview + publish tooling).
# Must exist at the path configured in the Cloud Agent environment `install` command.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$ROOT/requirements.txt" ]]; then
  echo "kdp-studio/requirements.txt not present at $ROOT; skipping install"
  exit 0
fi

python3 -m pip install --upgrade pip -q
python3 -m pip install --user -r "$ROOT/requirements.txt" -q

# Smoke-check imports that previously crashed Preview Studio / cover renders
python3 - <<'PY'
from PIL import Image  # noqa: F401
import fastapi  # noqa: F401
import uvicorn  # noqa: F401
import reportlab  # noqa: F401
import pypdf  # noqa: F401
print("kdp-studio deps OK")
PY

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
echo "cloud-agent-install complete"
