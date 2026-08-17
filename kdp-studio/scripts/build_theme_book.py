#!/usr/bin/env python3
"""Build a KDP coloring-book product from art-source PNGs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from kdp_studio.art_import import import_art_folder  # noqa: E402
from kdp_studio.build import build_interior_pdf  # noqa: E402
from kdp_studio.cover_art import PEN_NAME  # noqa: E402
from kdp_studio.cover_art import THEMES as COVER_THEMES  # noqa: E402
from kdp_studio.cover_art import render_theme_cover  # noqa: E402
from kdp_studio.pricing import research_and_price  # noqa: E402
from kdp_studio.publish import build_publish_package  # noqa: E402
from kdp_studio.specs import ROOT, product_dir  # noqa: E402
from kdp_studio.validate import validate_product  # noqa: E402

COVER_HEROES = ROOT / "assets" / "covers"

# Only Quiet Places — see STYLE.md. Do not add other art styles or theme SKUs here
# unless they follow that foundation exactly.
THEMES = {
    "quiet-places-40": {
        "title": "Quiet Places",
        "subtitle": "40 Bold & Easy Designs for Stress Relief",
        "one_liner": "Cozy landscapes, flowers, mushrooms, and calm little scenes in big bold outlines.",
        "audience": "Adults and kids who want simple, relaxing coloring without tiny details",
        "keywords": [
            "bold and easy coloring book",
            "stress relief coloring",
            "simple landscapes coloring",
            "easy coloring for adults",
            "cozy scenes coloring book",
            "relaxation coloring pages",
            "large print coloring book",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Self-Help > Stress Management",
        ],
        "query": "bold and easy coloring book stress relief landscapes",
        "cover_rgb": ((230, 240, 235), (50, 90, 70)),
        "trim": "square",
        "designs": 40,
    },
}


def ensure_meta(slug: str) -> dict:
    cfg = THEMES[slug]
    root = product_dir(slug)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pages").mkdir(exist_ok=True)
    (root / "cover").mkdir(exist_ok=True)
    (root / "art-source").mkdir(exist_ok=True)
    designs = int(cfg.get("designs", 30))
    trim = str(cfg.get("trim", "letter"))
    trim_label = "8.5 x 8.5 inch square" if trim == "square" else "8.5 x 11 inch paperback"
    meta = {
        "id": slug,
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "type": "coloring-book",
        "theme": slug.rsplit("-", 1)[0],
        "trim": trim,
        "bleed": False,
        "single_sided": True,
        "designs": designs,
        "page_count_interior": None,
        "paper_color": "white",
        "ink": "black",
        "cover_finish": "matte",
        "list_price_usd": 9.99,
        "audience": cfg["audience"],
        "one_liner": cfg["one_liner"],
        "description": (
            f"{cfg['one_liner']} {designs} original pages with bold outlines and closed shapes "
            "ready to color. Single-sided so markers stay on one design. "
            "AI-assisted artwork — disclose on KDP upload."
        ),
        "bullets": [
            f"{designs} unique pages",
            "Bold line art with closed shapes",
            "Single-sided pages for markers",
            f"{trim_label} format",
            "Relaxing designs for adults and kids",
            "AI-assisted art (disclose on KDP)",
        ],
        "keywords": cfg["keywords"],
        "categories": cfg["categories"],
        "author": PEN_NAME,
        "ai_assisted": True,
        "art_source": "art-source",
        "status": "draft",
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (root / "brief.md").write_text(
        f"# {cfg['title']}\n\n**Slug:** `{slug}`  \n**Author:** {PEN_NAME}\n\n{cfg['one_liner']}\n",
        encoding="utf-8",
    )
    listing_dir = ROOT / "launch" / "listings"
    listing_dir.mkdir(parents=True, exist_ok=True)
    (listing_dir / f"{slug}.md").write_text(
        f"# {cfg['title']} — {cfg['subtitle']}\n\n"
        f"**Author:** {PEN_NAME}\n"
        f"**Price target:** comps research\n"
        f"**AI-assisted:** Yes\n\n"
        f"## Description\n\n{meta['description']}\n",
        encoding="utf-8",
    )
    return meta


def render_cover(
    slug: str,
    page_count: int,
    hero_art: Path | None = None,
    trim: str | None = None,
) -> Path:
    cfg = THEMES[slug]
    root = product_dir(slug)
    cover_meta = COVER_THEMES.get(slug, {})
    hero_name = cover_meta.get("hero")
    hero = COVER_HEROES / hero_name if hero_name else None
    if hero is None or not hero.exists():
        # Fall back to first art-source page (should rarely happen)
        hero = hero_art or next(sorted((root / "art-source").glob("*.png")))
    # Keep a copy beside the wrap for publish packages / re-renders
    local_hero = root / "cover" / "hero.png"
    local_hero.parent.mkdir(parents=True, exist_ok=True)
    local_hero.write_bytes(Path(hero).read_bytes())
    meta_path = root / "meta.json"
    author = PEN_NAME
    trim_key = trim or str(cfg.get("trim", "letter"))
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        author = meta.get("author") or PEN_NAME
        trim_key = str(meta.get("trim") or trim_key)
        if meta.get("author") != PEN_NAME:
            meta["author"] = PEN_NAME
            author = PEN_NAME
            meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    out = root / "cover" / "wrap-placeholder.png"
    render_theme_cover(
        slug=slug,
        title=cfg["title"],
        subtitle=cfg["subtitle"],
        one_liner=cfg["one_liner"],
        page_count=page_count,
        hero_path=local_hero,
        out_path=out,
        author=author,
        trim=trim_key,
    )
    return out


def build_slug(slug: str) -> dict:
    if slug not in THEMES:
        raise SystemExit(f"Unknown slug {slug}. Choose from: {', '.join(THEMES)}")
    cfg = THEMES[slug]
    designs = int(cfg.get("designs", 30))
    trim = str(cfg.get("trim", "letter"))
    ensure_meta(slug)
    root = product_dir(slug)
    art_dir = root / "art-source"
    pngs = sorted(art_dir.glob("*.png"))
    if len(pngs) < designs:
        return {
            "ok": False,
            "slug": slug,
            "error": f"Need {designs} PNGs in {art_dir}, found {len(pngs)}",
        }

    # Keep only first N sorted for stable page order
    for extra in pngs[designs:]:
        extra.unlink()
    paths = import_art_folder(art_dir, root / "pages", trim=trim, theme=slug)
    for p in sorted((root / "pages").glob("page-*.png"))[designs:]:
        p.unlink()
    for p in sorted((root / "pages").glob("page-*.svg"))[designs:]:
        p.unlink()
    paths = sorted((root / "pages").glob("page-*.png"))[:designs]

    result = build_interior_pdf(paths, root / "interior.pdf", trim=trim, single_sided=True)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    meta["page_count_interior"] = result["page_count"]
    meta["designs"] = len(paths)
    meta["trim"] = trim
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    render_cover(slug, result["page_count"], trim=trim)
    research_and_price(slug, query=cfg["query"], apply=True, allow_demo=True)
    errors = validate_product(slug)
    pkg = build_publish_package(slug) if not errors else {"ok": False, "errors": errors}
    return {
        "ok": not errors and pkg.get("ok"),
        "slug": slug,
        "pages": len(paths),
        "validation": errors,
        "publish": pkg.get("package_dir"),
    }


def rebuild_covers_only(slug: str) -> dict:
    """Re-render cover wrap + publish package without regenerating interiors."""
    if slug not in THEMES:
        raise SystemExit(f"Unknown slug {slug}. Choose from: {', '.join(THEMES)}")
    root = product_dir(slug)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    pages = int(meta.get("page_count_interior") or 60)
    out = render_cover(slug, pages)
    pkg = build_publish_package(slug)
    return {"ok": True, "slug": slug, "cover": str(out), "publish": pkg.get("package_dir")}


if __name__ == "__main__":
    args = sys.argv[1:]
    covers_only = False
    if args and args[0] == "--covers-only":
        covers_only = True
        args = args[1:]
    slugs = args or list(THEMES)
    for slug in slugs:
        result = rebuild_covers_only(slug) if covers_only else build_slug(slug)
        print(json.dumps(result, indent=2))
