#!/usr/bin/env python3
"""Bundle KDP Studio upload kits + a machine-readable manifest for migration.

Writes (committed):
  kdp-studio/migration/manifest.json
  kdp-studio/migration/INDEX.md
  kdp-studio/migration/CHECKSUMS.sha256

Writes (not committed):
  kdp-studio-migration.tar.gz  under the first writable of /tmp, /workspace,
  kdp-studio/migration. /opt/cursor/artifacts is often a 0-byte store mount
  and is skipped unless a write probe succeeds.

Re-run after checkout to rebuild the tarball from products/*/publish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PRODUCTS = ROOT / "products"
COVERS = ROOT / "assets" / "covers"
OUT_DIR = ROOT / "migration"
OUT_MANIFEST = OUT_DIR / "manifest.json"
OUT_INDEX = OUT_DIR / "INDEX.md"
OUT_CHECKSUMS = OUT_DIR / "CHECKSUMS.sha256"

# Scene-registered titles that do not yet have a built product folder.
PENDING_INTERIORS = [
    ("celestial-40", "Celestial Mandalas"),
    ("cozy-critters-40", "Cozy Critters"),
    ("dragons-40", "Dragons"),
    ("spooky-cute-40", "Spooky Cute"),
    ("holidays-40", "Holidays"),
    ("chapel-gardens-40", "Chapel Gardens"),
    ("slow-mornings-40", "Slow Mornings"),
    ("moon-magic-40", "Moon Magic"),
    ("dark-academia-40", "Dark Academia"),
    ("zen-gardens-40", "Zen Gardens"),
    ("retro-40", "Retro Days"),
    ("rest-easy-40", "Rest Easy"),
    ("dinosaurs-40", "Dinosaurs"),
    ("star-signs-40", "Star Signs"),
]

COVER_HERO_ALIASES = {
    "quiet-places": "quiet",
}


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _meta(slug_dir: Path) -> dict:
    path = slug_dir / "meta.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cover_hero(slug: str) -> Path | None:
    base = slug.removesuffix("-40")
    name = COVER_HERO_ALIASES.get(base, base)
    path = COVERS / f"cover-hero-{name}.png"
    return path if path.is_file() else None


def _writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".kdp-write-probe-{os.getpid()}"
        probe.write_bytes(b"ok")
        probe.unlink()
        return True
    except OSError:
        return False


def pick_tarball_dir() -> Path:
    artifacts = Path("/opt/cursor/artifacts")
    for candidate in (Path("/tmp"), Path("/workspace"), OUT_DIR, artifacts):
        if _writable_dir(candidate):
            # Skip the artifacts store when it reports zero capacity.
            if candidate == artifacts:
                try:
                    st = os.statvfs(candidate)
                    if st.f_blocks == 0 or st.f_bavail == 0:
                        continue
                except OSError:
                    continue
            return candidate
    return Path("/tmp")


def collect() -> dict:
    skus = []
    checksum_rows: list[tuple[str, str]] = []
    for product in sorted(PRODUCTS.iterdir()):
        if not product.is_dir():
            continue
        meta = _meta(product)
        pub = product / "publish"
        pages = sorted((product / "pages").glob("page-*.png")) if (product / "pages").is_dir() else []
        art = sorted((product / "art-source").glob("*.png")) if (product / "art-source").is_dir() else []
        interior = pub / "interior.pdf"
        wrap = pub / "cover" / "wrap-placeholder.png"
        fields = pub / "kdp-fields.json"
        hero = _cover_hero(product.name)
        files = {
            "interior.pdf": interior,
            "wrap": wrap,
            "kdp-fields.json": fields,
        }
        hashes = {}
        for label, path in files.items():
            digest = _sha256(path)
            hashes[label] = digest
            if digest:
                checksum_rows.append((digest, str(path.relative_to(ROOT))))
        skus.append(
            {
                "slug": product.name,
                "title": meta.get("title") or product.name,
                "subtitle": meta.get("subtitle"),
                "author": meta.get("author", "Elsie Wren"),
                "designs": meta.get("designs"),
                "trim": meta.get("trim"),
                "list_price_usd": meta.get("list_price_usd"),
                "ai_assisted": meta.get("ai_assisted"),
                "status": meta.get("status", "draft"),
                "page_pngs": len(pages),
                "art_source_pngs": len(art),
                "has_interior_pdf": interior.is_file(),
                "has_wrap": wrap.is_file(),
                "has_kdp_fields": fields.is_file(),
                "publish_dir": str(pub.relative_to(ROOT)) if pub.is_dir() else None,
                "cover_hero": str(hero.relative_to(ROOT)) if hero else None,
                "sha256": hashes,
                "ready_to_upload": interior.is_file() and fields.is_file() and wrap.is_file(),
            }
        )
    pending = []
    for slug, title in PENDING_INTERIORS:
        hero = _cover_hero(slug)
        pending.append(
            {
                "slug": slug,
                "title": title,
                "cover_hero": str(hero.relative_to(ROOT)) if hero else None,
                "listing": f"launch/listings/{slug}.md"
                if (ROOT / "launch" / "listings" / f"{slug}.md").is_file()
                else None,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pen_name": "Elsie Wren",
        "style": "STYLE.md bold-and-easy Quiet Places foundation",
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_commit": _git("rev-parse", "HEAD"),
        "source_branch": "cursor/trend-coloring-books-9aff",
        "skus": skus,
        "pending_interiors": pending,
        "checksum_rows": checksum_rows,
        "known_issues": [
            "User reported sizing issues and random missing lines across books; QA pass not finished.",
            "Do not buy barcodes. Leave the 2.0x1.2 in well empty; KDP prints a free EAN-13.",
            "Disclose AI on the KDP form, never as printed wrap text.",
            "Never letters/words/numbers on interiors. Never grayscale, hatching, or solid black fills.",
        ],
        "resume": {
            "checkout": "git fetch origin cursor/kdp-migration-package-9aff && git checkout cursor/kdp-migration-package-9aff",
            "preview": "cd kdp-studio/tools && python3 -m kdp_studio preview --host 0.0.0.0 --port 8765",
            "inkify_slot": "from inkify_bold_easy import to_ink; to_ink(src, dest)  # never CLI glob (renumbers)",
            "build": "python3 scripts/build_theme_book.py <slug>",
            "package": "python3 scripts/package_migration.py",
        },
    }


def write_index(manifest: dict) -> None:
    ready = [s for s in manifest["skus"] if s["ready_to_upload"]]
    lines = [
        "# KDP Studio migration index",
        "",
        f"Generated `{manifest['generated_at']}` from `{manifest.get('git_branch')}` @ `{manifest.get('git_commit', '')[:12]}`.",
        "",
        f"Pen name **{manifest['pen_name']}**. {len(ready)} of {len(manifest['skus'])} product folders are upload-ready.",
        "",
        "## Upload-ready SKUs",
        "",
        "| Slug | Title | Price | Pages | Interior SHA256 (12) |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for sku in ready:
        sha = (sku.get("sha256") or {}).get("interior.pdf") or ""
        lines.append(
            f"| `{sku['slug']}` | {sku['title']} | ${sku.get('list_price_usd')} | {sku['page_pngs']} | `{sha[:12]}` |"
        )
    lines += [
        "",
        "## Registered titles without interiors",
        "",
        "| Slug | Title | Cover hero |",
        "| --- | --- | --- |",
    ]
    for item in manifest["pending_interiors"]:
        hero = item.get("cover_hero") or "—"
        lines.append(f"| `{item['slug']}` | {item['title']} | `{hero}` |")
    lines += [
        "",
        "Rebuild this folder with `python3 kdp-studio/scripts/package_migration.py`.",
        "The tarball is not committed; see `MIGRATION.md`.",
        "",
    ]
    OUT_INDEX.write_text("\n".join(lines), encoding="utf-8")


def write_checksums(manifest: dict) -> None:
    rows = manifest.pop("checksum_rows", [])
    body = "".join(f"{digest}  {rel}\n" for digest, rel in rows)
    OUT_CHECKSUMS.write_text(body, encoding="utf-8")


def write_tarball(manifest: dict, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    if tmp.exists():
        tmp.unlink()
    with tarfile.open(tmp, "w:gz") as tar:
        tar.add(OUT_MANIFEST, arcname="kdp-studio-migration/manifest.json")
        tar.add(OUT_INDEX, arcname="kdp-studio-migration/INDEX.md")
        tar.add(OUT_CHECKSUMS, arcname="kdp-studio-migration/CHECKSUMS.sha256")
        for name in ("STYLE.md", "README.md", "MIGRATION.md", "requirements.txt"):
            path = ROOT / name
            if path.exists():
                tar.add(path, arcname=f"kdp-studio-migration/{name}")
        listings = ROOT / "launch"
        if listings.is_dir():
            tar.add(listings, arcname="kdp-studio-migration/launch")
        if COVERS.is_dir():
            tar.add(COVERS, arcname="kdp-studio-migration/covers")
        for sku in manifest["skus"]:
            pub = ROOT / sku["publish_dir"] if sku.get("publish_dir") else None
            if pub and pub.is_dir():
                tar.add(pub, arcname=f"kdp-studio-migration/publish/{sku['slug']}")
    tmp.replace(dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-tarball", action="store_true", help="Write inventory files only")
    parser.add_argument("--tarball-dir", type=Path, default=None)
    args = parser.parse_args()

    manifest = collect()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_checksums(manifest)
    payload = {k: v for k, v in manifest.items() if k != "checksum_rows"}
    OUT_MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_index(payload)

    tarball = None
    if not args.no_tarball:
        out_dir = args.tarball_dir or pick_tarball_dir()
        dest = out_dir / "kdp-studio-migration.tar.gz"
        try:
            tarball = write_tarball(payload, dest)
        except OSError as exc:
            print(f"tarball failed ({exc}); inventory files were still written")

    ready = sum(1 for s in payload["skus"] if s["ready_to_upload"])
    print(f"manifest:  {OUT_MANIFEST}")
    print(f"index:     {OUT_INDEX}")
    print(f"checksums: {OUT_CHECKSUMS}")
    if tarball:
        print(f"tarball:   {tarball} ({tarball.stat().st_size} bytes)")
    else:
        print("tarball:   skipped")
    print(f"SKUs ready to upload: {ready}/{len(payload['skus'])}")
    print(f"pending interiors: {len(payload['pending_interiors'])}")


if __name__ == "__main__":
    main()
