"""Prepare a KDP upload package and optional browser-assisted publish steps.

Amazon does not offer a public KDP upload API for indie publishers.
This module:
  1) builds a complete publish package (files + field checklist)
  2) can launch a guided browser session (Playwright) — dry-run by default

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
            "page_count_interior": meta.get("page_count_interior"),
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
    checklist.write_text(
        "\n".join(
            [
                f"# Upload checklist — {meta.get('title')}",
                "",
                "Amazon KDP does **not** provide a public API for paperback uploads.",
                "Use this package in [KDP Bookshelf](https://kdp.amazon.com/en_US/bookshelf).",
                "",
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
        ),
        encoding="utf-8",
    )

    return {"ok": True, "package_dir": str(out), "fields": fields}


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
        # Leave browser open briefly for manual login; caller closes.
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
