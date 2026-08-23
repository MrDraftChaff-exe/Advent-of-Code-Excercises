#!/usr/bin/env bash
# Re-download a fresh public snapshot from the live site into ./site
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
SITE_URL="${SITE_URL:-https://featherhillmainecoons.com}"

PAGES=(
  "$SITE_URL/"
  "$SITE_URL/about-us/"
  "$SITE_URL/past-kittens/"
  "$SITE_URL/available-kittens/"
  "$SITE_URL/contact/"
  "$SITE_URL/our-queens-and-toms/"
)

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "Mirroring $SITE_URL ..."
mkdir -p "$TMP/mirror"
(
  cd "$TMP/mirror"
  wget \
    --recursive \
    --level=5 \
    --page-requisites \
    --convert-links \
    --adjust-extension \
    --no-parent \
    --no-host-directories \
    --domains=featherhillmainecoons.com \
    --exclude-directories=/wp-admin \
    --reject='wp-login.php,xmlrpc.php,*logout*' \
    --wait=0.2 \
    --random-wait \
    --timeout=30 \
    --tries=3 \
    --user-agent='Mozilla/5.0 (compatible; LocalArchive/1.0)' \
    -e robots=off \
    "${PAGES[@]}"
)

echo "Normalizing filenames and links..."
python3 "$ROOT/scripts/normalize_mirror.py" "$TMP/mirror"

echo "Replacing ./site ..."
rm -rf "$ROOT/site"
mkdir -p "$ROOT/site"
cp -a "$TMP/mirror/." "$ROOT/site/"
echo "Done. Run: ./scripts/serve.sh"
