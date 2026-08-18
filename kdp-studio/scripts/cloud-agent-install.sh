#!/usr/bin/env bash
# Idempotent Cloud Agent install for KDP Studio (Preview + publish tooling).
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="/workspace/kdp-studio"
if [[ ! -d "$ROOT" ]]; then
  echo "kdp-studio not found at $ROOT" >&2
  exit 1
fi

python3 -m pip install --upgrade pip -q
python3 -m pip install -r "$ROOT/requirements.txt" -q

# Smoke-check the imports that previously crashed Preview Studio
python3 - <<'PY'
from PIL import Image  # noqa: F401
import fastapi  # noqa: F401
import uvicorn  # noqa: F401
print("kdp-studio deps OK")
PY

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
echo "cloud-agent-install complete"
