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

# Import shared scene metadata for titles etc.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme_scenes import THEMES as SCENE_THEMES  # noqa: E402

COVER_HEROES = ROOT / "assets" / "covers"

# All titles follow STYLE.md bold-and-easy foundation (Quiet Places look).
THEMES: dict = {
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

for slug, cfg in SCENE_THEMES.items():
    THEMES[slug] = {
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "one_liner": cfg["one_liner"],
        "audience": "Adults and kids who want simple, relaxing bold-and-easy coloring",
        "keywords": cfg["keywords"],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Self-Help > Stress Management",
        ],
        "query": cfg["query"],
        "cover_rgb": cfg["cover_rgb"],
        "trim": "square",
        "designs": 40,
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
        "list_price_usd": 10.99,
        "audience": cfg["audience"],
        "one_liner": cfg["one_liner"],
        "description": (
            f"{cfg['one_liner']} {designs} big, bold, easy pages in {trim_label} format. "
            "Single-sided printing. Original designs. AI-assisted line art disclosed on KDP."
        ),
        "bullets": [
            f"{designs} original bold-and-easy designs",
            "Single-sided pages for markers",
            f"{trim_label} trim, KDP paperback ready",
            "Thick closed outlines, no tiny detail stress",
            "No trademarks — original scenes only",
        ],
        "keywords": cfg["keywords"],
        "categories": cfg["categories"],
        "ai_assisted": True,
        "status": "draft",
        "author": PEN_NAME,
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    brief = root / "brief.md"
    if not brief.exists():
        brief.write_text(
            f"# {meta['title']}\n\n{meta['one_liner']}\n\n"
            f"Follow `STYLE.md`. Build: `python3 scripts/build_theme_book.py {slug}`\n",
            encoding="utf-8",
        )
    return meta


def build_one(slug: str, *, covers_only: bool = False) -> dict:
    cfg = THEMES[slug]
    root = product_dir(slug)
    meta = ensure_meta(slug)
    trim = str(cfg.get("trim", "letter"))
    designs = int(cfg.get("designs", 40))
    if not covers_only:
        art_dir = root / "art-source"
        paths = import_art_folder(art_dir, root / "pages", trim=trim, theme=slug)
        result = build_interior_pdf(paths, root / "interior.pdf", trim=trim, single_sided=True)
        # single-sided → designs*2 interior pages for cover spine
        page_count = int(result.get("page_count", designs * 2))
    else:
        result = {"ok": True, "pages": 0}
        page_count = designs * 2

    cover_meta = COVER_THEMES.get(slug, {})
    hero_name = cover_meta.get("hero", f"cover-hero-{slug}.png")
    hero = COVER_HEROES / hero_name
    if not hero.exists():
        # fallback soft gradient hero
        from PIL import Image as _Image

        hero = root / "cover" / "_tmp_hero.png"
        _Image.new("RGB", (1200, 1200), cfg.get("cover_rgb", ((220, 230, 240), (80, 100, 120)))[0]).save(hero)

    render_theme_cover(
        slug=slug,
        title=cfg["title"],
        subtitle=cfg["subtitle"],
        one_liner=cfg["one_liner"],
        page_count=page_count,
        hero_path=hero,
        out_path=root / "cover" / "wrap-placeholder.png",
        trim=trim,
        paper="white",
    )
    try:
        research_and_price(slug, query=cfg.get("query", cfg["title"]), apply=True)
    except Exception as exc:  # noqa: BLE001
        print(f"price skip: {exc}")
    build_publish_package(slug)
    validation = validate_product(slug)
    return {
        "ok": True,
        "slug": slug,
        "pages": designs,
        "validation": validation,
        "publish": str(root / "publish"),
        **result,
    }


def main(args: list[str] | None = None) -> None:
    args = list(args if args is not None else sys.argv[1:])
    covers_only = False
    if "--covers-only" in args:
        covers_only = True
        args.remove("--covers-only")
    if args and args[0] not in THEMES and args[0] != "--all":
        raise SystemExit(f"Unknown slug {args[0]}. Choose from: {', '.join(THEMES)}")
    if not args or args == ["--all"]:
        slugs = list(THEMES)
    else:
        slugs = args
    for slug in slugs:
        if slug not in THEMES:
            raise SystemExit(f"Unknown slug {slug}. Choose from: {', '.join(THEMES)}")
        print(json.dumps(build_one(slug, covers_only=covers_only), indent=2))


if __name__ == "__main__":
    main()
