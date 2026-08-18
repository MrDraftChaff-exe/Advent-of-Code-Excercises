"""Prepare a KDP upload package and optional browser-assisted publish steps.

Amazon does not offer a public KDP upload API for indie publishers.
This module:
  1) builds a complete publish package (files + field checklist)
  2) stages a numbered upload-kit folder with paste-ready field files
  3) can launch a guided browser session (Playwright) — dry-run by default

Live form automation against kdp.amazon.com is experimental, brittle, and may
conflict with Amazon terms. Prefer manual upload using the package + Preview Studio.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .specs import ROOT, product_dir
from .validate import validate_product


def build_publish_package(slug: str) -> dict[str, Any]:
    errors = validate_product(slug)
    if errors:
        return {"ok": False, "errors": errors}

    root = product_dir(slug)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    pricing = {}
    pricing_path = root / "pricing.json"
    if pricing_path.exists():
        pricing = json.loads(pricing_path.read_text(encoding="utf-8"))

    out = root / "publish"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    files_copied: list[str] = []
    for name in ("interior.pdf", "meta.json", "pricing.json", "brief.md"):
        src = root / name
        if src.exists():
            shutil.copy2(src, out / name)
            files_copied.append(name)

    cover_src = root / "cover"
    if cover_src.exists():
        cover_dst = out / "cover"
        shutil.copytree(cover_src, cover_dst)
        files_copied.append("cover/")

    listing = ROOT / "launch" / "listings" / f"{slug}.md"
    if listing.exists():
        shutil.copy2(listing, out / "listing.md")
        files_copied.append("listing.md")

    dims = {}
    dims_path = root / "cover" / "dimensions.json"
    if dims_path.exists():
        dims = json.loads(dims_path.read_text(encoding="utf-8"))

    # Prefer live PDF page count when meta is stale/null
    page_count = meta.get("page_count_interior")
    interior = root / "interior.pdf"
    if interior.exists():
        try:
            from pypdf import PdfReader

            page_count = len(PdfReader(str(interior)).pages)
        except Exception:
            pass

    fields = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kdp_url": "https://kdp.amazon.com/en_US/bookshelf",
        "official_api": False,
        "note": (
            "KDP has no public upload API. Upload these files manually in Bookshelf, "
            "or use `kdp_studio publish --assist` for an experimental guided browser session."
        ),
        "paperback": {
            "title": meta.get("title"),
            "subtitle": meta.get("subtitle"),
            "description": meta.get("description"),
            "author": meta.get("author") or "Your Name",
            "keywords": meta.get("keywords") or [],
            "categories": meta.get("categories") or [],
            "ai_assisted": bool(meta.get("ai_assisted")),
            "trim": meta.get("trim"),
            "ink": meta.get("ink", "black"),
            "paper_color": meta.get("paper_color", "white"),
            "cover_finish": meta.get("cover_finish", "matte"),
            "bleed": bool(meta.get("bleed", False)),
            "page_count_interior": page_count,
            "list_price_usd": (
                pricing.get("recommendation", {}).get("list_price_usd")
                or meta.get("list_price_usd")
            ),
            "manuscript_file": "interior.pdf",
            "cover_file_hint": "cover/wrap-placeholder.png (replace with final wrap PDF/PNG)",
            "cover_dimensions": dims,
        },
        "pricing_research": pricing.get("recommendation"),
        "comps_source": pricing.get("source"),
        "files": files_copied,
    }
    (out / "kdp-fields.json").write_text(json.dumps(fields, indent=2) + "\n", encoding="utf-8")

    checklist = out / "UPLOAD.md"
    lines = [
        f"# Upload checklist — {meta.get('title')}",
        "",
        "Amazon KDP does **not** provide a public API for paperback uploads.",
        "Use this package in [KDP Bookshelf](https://kdp.amazon.com/en_US/bookshelf).",
        "",
    ]
    if slug == "buildings-40":
        lines += [
            "## Fastest path",
            "",
            "```bash",
            "./scripts/upload-buildings.sh",
            "```",
            "",
            "Or in Preview Studio → Publish → **Stage upload kit**.",
            "",
            "Stages `products/buildings-40/upload-kit/` with numbered files + paste-ready fields.",
            "",
        ]
    lines += [
        "## Steps",
        "1. Create paperback → paste title / subtitle / description from `kdp-fields.json`",
        "2. Keywords + categories from the same file",
        "3. Disclose AI content if `ai_assisted` is true",
        "4. Upload `interior.pdf` as manuscript",
        "5. Upload final cover wrap sized per `cover/dimensions.json`",
        f"6. Set list price to **${fields['paperback']['list_price_usd']}** (from comps research if run)",
        "7. Proof in KDP Previewer, then publish",
        "",
        "## Optional assist",
        "```bash",
        f"python3 -m kdp_studio publish --slug {slug} --assist",
        "```",
        "Dry-run opens a guided checklist browser page. `--live` is experimental.",
        "",
    ]
    checklist.write_text("\n".join(lines), encoding="utf-8")

    return {"ok": True, "package_dir": str(out), "fields": fields}


def stage_upload_kit(slug: str) -> dict[str, Any]:
    """Refresh publish package and stage a numbered upload-kit with paste-ready fields."""
    pkg = build_publish_package(slug)
    if not pkg.get("ok"):
        return pkg

    root = product_dir(slug)
    publish = root / "publish"
    kit = root / "upload-kit"
    if kit.exists():
        shutil.rmtree(kit)
    kit.mkdir(parents=True)

    files: list[str] = []
    shutil.copy2(publish / "interior.pdf", kit / "01-manuscript-interior.pdf")
    files.append("01-manuscript-interior.pdf")

    cover_png = root / "cover" / "wrap-placeholder.png"
    if cover_png.exists():
        shutil.copy2(cover_png, kit / "02-cover-wrap-placeholder.png")
        files.append("02-cover-wrap-placeholder.png")

    shutil.copy2(publish / "kdp-fields.json", kit / "03-kdp-fields.json")
    files.append("03-kdp-fields.json")

    if (publish / "listing.md").exists():
        shutil.copy2(publish / "listing.md", kit / "04-listing-copy.md")
        files.append("04-listing-copy.md")

    dims_path = root / "cover" / "dimensions.json"
    if dims_path.exists():
        shutil.copy2(dims_path, kit / "05-cover-dimensions.json")
        files.append("05-cover-dimensions.json")

    shutil.copy2(publish / "UPLOAD.md", kit / "00-READ-ME-FIRST.md")
    files.append("00-READ-ME-FIRST.md")

    pb = pkg["fields"]["paperback"]
    dims = pb.get("cover_dimensions") or {}
    keywords = pb.get("keywords") or []
    categories = pb.get("categories") or []
    description = str(pb.get("description") or "")

    paste = {
        "title": str(pb.get("title") or ""),
        "subtitle": str(pb.get("subtitle") or ""),
        "author": str(pb.get("author") or ""),
        "description": description,
        "keywords": "\n".join(keywords),
        "categories": "\n".join(categories),
        "list_price_usd": str(pb.get("list_price_usd") or ""),
        "ai_assisted": "YES — disclose AI-assisted content on KDP"
        if pb.get("ai_assisted")
        else "no",
        "trim": "8.5 x 8.5 in (square), black ink, white paper, matte cover, no bleed",
    }
    paste_dir = kit / "paste-fields"
    paste_dir.mkdir()
    for key, value in paste.items():
        (paste_dir / f"{key}.txt").write_text(value + ("\n" if value else ""), encoding="utf-8")
        files.append(f"paste-fields/{key}.txt")

    title = pb.get("title") or slug
    guide = [
        f"# {title} — upload in 5 minutes",
        "",
        "Open https://kdp.amazon.com/en_US/bookshelf → Create → Paperback.",
        "",
        "## Paste these fields (also in `paste-fields/*.txt`)",
        f"- **Title:** {paste['title']}",
        f"- **Subtitle:** {paste['subtitle']}",
        f"- **Author:** {paste['author']}",
        f"- **List price:** ${paste['list_price_usd']}",
        f"- **AI assisted:** {paste['ai_assisted']}",
        f"- **Trim / print:** {paste['trim']}",
        f"- **Interior pages:** {pb.get('page_count_interior')}",
        "",
        "### Description (copy all)",
        "",
        description,
        "",
        "### Keywords (one per KDP slot)",
        "",
        *[f"- {k}" for k in keywords],
        "",
        "### Categories",
        "",
        *[f"- {c}" for c in categories],
        "",
        "## Upload these files (in order)",
        "1. **Manuscript:** `01-manuscript-interior.pdf`",
        "2. **Cover:** final wrap sized "
        f"{dims.get('cover_width_in')}×{dims.get('cover_height_in')} in "
        f"({dims.get('cover_width_px')}×{dims.get('cover_height_px')} px @ 300 dpi) — "
        "start from `02-cover-wrap-placeholder.png` (replace before going live if needed)",
        "",
        "## Then",
        "- Run KDP Previewer",
        "- Publish (or save draft)",
        "",
        "Full JSON: `03-kdp-fields.json`",
    ]
    (kit / "00-UPLOAD-NOW.md").write_text("\n".join(guide) + "\n", encoding="utf-8")
    files.append("00-UPLOAD-NOW.md")

    return {
        "ok": True,
        "slug": slug,
        "kit_dir": str(kit),
        "package_dir": str(publish),
        "files": sorted(files),
        "fields": pkg["fields"],
        "kdp_bookshelf": "https://kdp.amazon.com/en_US/bookshelf",
        "paste_fields": paste,
    }


def run_assist(slug: str, *, live: bool = False) -> dict[str, Any]:
    """Guided assist. Default dry-run opens local checklist; --live tries Playwright login page only."""
    pkg = build_publish_package(slug)
    if not pkg.get("ok"):
        return pkg

    if not live:
        return {
            "ok": True,
            "mode": "dry-run",
            "message": (
                "Publish package ready. Open Preview Studio → Publish tab, or see "
                f"{pkg['package_dir']}/UPLOAD.md. Pass --live only for experimental browser assist."
            ),
            "package_dir": pkg["package_dir"],
            "kdp_bookshelf": "https://kdp.amazon.com/en_US/bookshelf",
        }

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "ok": False,
            "mode": "live",
            "error": "Playwright not installed. Run: python3 -m pip install playwright && playwright install chromium",
            "package_dir": pkg["package_dir"],
        }

    # Experimental: open Bookshelf so the publisher can paste from kdp-fields.json.
    # Full unattended form-filling is intentionally not implemented — KDP UI changes often
    # and automated publishing can violate Amazon terms.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://kdp.amazon.com/en_US/bookshelf", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        browser.close()

    return {
        "ok": True,
        "mode": "live-open-bookshelf",
        "message": (
            "Opened KDP Bookshelf (experimental). Complete upload manually using "
            f"{pkg['package_dir']}/kdp-fields.json — unattended auto-fill is not supported."
        ),
        "package_dir": pkg["package_dir"],
    }
