#!/usr/bin/env bash
# One-command KDP upload kit for Buildings (buildings-40).
# Refreshes the publish package, validates, and stages a folder you can upload from.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="buildings-40"
PUBLISH="$ROOT/products/$SLUG/publish"
KIT="$ROOT/products/$SLUG/upload-kit"
TOOLS="$ROOT/tools"

cd "$TOOLS"

echo "==> Refresh publish package for $SLUG"
python3 -m kdp_studio publish --slug "$SLUG"

echo "==> Validate"
python3 -m kdp_studio validate --slug "$SLUG"

echo "==> Stage upload kit at $KIT"
rm -rf "$KIT"
mkdir -p "$KIT"
cp -f "$PUBLISH/interior.pdf" "$KIT/01-manuscript-interior.pdf"
if [[ -f "$ROOT/products/$SLUG/cover/wrap-placeholder.png" ]]; then
  cp -f "$ROOT/products/$SLUG/cover/wrap-placeholder.png" "$KIT/02-cover-wrap-placeholder.png"
fi
cp -f "$PUBLISH/kdp-fields.json" "$KIT/03-kdp-fields.json"
cp -f "$PUBLISH/UPLOAD.md" "$KIT/00-READ-ME-FIRST.md"
cp -f "$PUBLISH/listing.md" "$KIT/04-listing-copy.md" 2>/dev/null || true
if [[ -f "$ROOT/products/$SLUG/cover/dimensions.json" ]]; then
  cp -f "$ROOT/products/$SLUG/cover/dimensions.json" "$KIT/05-cover-dimensions.json"
fi

# Friendly human checklist
python3 - <<PY
import json
from pathlib import Path
fields = json.loads(Path("$PUBLISH/kdp-fields.json").read_text())
pb = fields["paperback"]
price = pb.get("list_price_usd")
dims = pb.get("cover_dimensions") or {}
lines = [
    "# Buildings — upload in 5 minutes",
    "",
    "Open https://kdp.amazon.com/en_US/bookshelf → Create → Paperback.",
    "",
    "## Paste these fields",
    f"- **Title:** {pb.get('title')}",
    f"- **Subtitle:** {pb.get('subtitle')}",
    f"- **Author:** {pb.get('author')}",
    f"- **Description:** (from 03-kdp-fields.json → paperback.description)",
    f"- **Keywords:** {', '.join(pb.get('keywords') or [])}",
    f"- **AI assisted:** {'YES — disclose' if pb.get('ai_assisted') else 'no'}",
    f"- **List price:** \${price}",
    f"- **Trim:** 8.5 × 8.5 in (square), black ink, white paper, matte cover, no bleed",
    "",
    "## Upload these files (in order)",
    "1. **Manuscript:** \`01-manuscript-interior.pdf\`",
    "2. **Cover:** final wrap sized "
    f"{dims.get('cover_width_in')}×{dims.get('cover_height_in')} in "
    f"({dims.get('cover_width_px')}×{dims.get('cover_height_px')} px @ 300 dpi) — "
    "replace the placeholder PNG before going live",
    "",
    "## Then",
    "- Run KDP Previewer",
    "- Publish (or save draft)",
    "",
    "Full JSON field dump: \`03-kdp-fields.json\`",
]
Path("$KIT/00-UPLOAD-NOW.md").write_text("\n".join(lines) + "\n")
print("Wrote", "$KIT/00-UPLOAD-NOW.md")
PY

echo
echo "Upload kit ready:"
ls -lh "$KIT"
echo
echo "Open Preview Studio → select Buildings → Publish tab, or upload from:"
echo "  $KIT"
echo "Quick read: $KIT/00-UPLOAD-NOW.md"
