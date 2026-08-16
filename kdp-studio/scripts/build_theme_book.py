#!/usr/bin/env python3
"""Build a KDP coloring-book product from art-source PNGs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from kdp_studio.art_import import import_art_folder  # noqa: E402
from kdp_studio.build import build_interior_pdf, cover_dimensions  # noqa: E402
from kdp_studio.pricing import research_and_price  # noqa: E402
from kdp_studio.publish import build_publish_package  # noqa: E402
from kdp_studio.specs import ROOT, product_dir  # noqa: E402
from kdp_studio.validate import validate_product  # noqa: E402

THEMES = {
    "forest-animals-30": {
        "title": "Forest Animals",
        "subtitle": "30 Woodland Friends to Color",
        "one_liner": "Foxes, owls, deer, and more — bold woodland animals ready to color.",
        "audience": "Kids, families, and adults who love nature and simple animal pages",
        "keywords": [
            "forest animals coloring book",
            "woodland animals",
            "kids coloring book",
            "fox deer owl",
            "nature coloring",
            "animal coloring pages",
            "wildlife coloring book",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Activities, Crafts & Games > Activity Books",
        ],
        "query": "forest animals coloring book for kids woodland",
        "cover_rgb": ((232, 240, 228), (45, 85, 50)),
    },
    "sports-30": {
        "title": "Sports",
        "subtitle": "30 Action Pages to Color",
        "one_liner": "Soccer balls, gear, and more — simple sports subjects ready to color.",
        "audience": "Kids and families who love sports and active play",
        "keywords": [
            "sports coloring book",
            "soccer basketball",
            "kids sports",
            "athletic coloring",
            "ball games",
            "sports activity book",
            "outdoor sports",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Activities, Crafts & Games > Activity Books",
        ],
        "query": "sports coloring book for kids",
        "cover_rgb": ((230, 236, 245), (28, 55, 110)),
        "animals_note": "soccer basketball baseball tennis swimming running cycling hockey trophy stadium",
    },
    "math-30": {
        "title": "Math Adventures",
        "subtitle": "30 Number & Shape Pages to Color",
        "one_liner": "Numbers, shapes, and simple math objects for curious colorists.",
        "audience": "Kids learning numbers and shapes; parents and teachers",
        "keywords": [
            "math coloring book",
            "numbers shapes",
            "educational coloring",
            "geometry for kids",
            "counting coloring",
            "math activity book",
            "learning numbers",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Education & Reference",
        ],
        "query": "math coloring book for kids numbers shapes",
        "cover_rgb": ((245, 236, 220), (120, 60, 20)),
    },
    "physical-science-30": {
        "title": "Physical Science",
        "subtitle": "30 Wonder Pages to Color",
        "one_liner": "Magnets, light bulbs, and simple science objects in bold line art.",
        "audience": "Curious kids and classrooms exploring how the world works",
        "keywords": [
            "science coloring book",
            "physical science kids",
            "STEM coloring",
            "magnets electricity",
            "science activity book",
            "physics for kids",
            "experiments coloring",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Education & Reference > Science & Nature",
        ],
        "query": "science coloring book for kids STEM",
        "cover_rgb": ((230, 240, 245), (20, 70, 100)),
    },
    "chemistry-30": {
        "title": "Chemistry Lab",
        "subtitle": "30 Molecule & Flask Pages to Color",
        "one_liner": "Beakers, flasks, and lab tools — simple chemistry objects to color.",
        "audience": "Kids and tweens curious about chemistry and lab science",
        "keywords": [
            "chemistry coloring book",
            "science lab kids",
            "molecules beakers",
            "STEM chemistry",
            "periodic table kids",
            "lab equipment coloring",
            "science activity",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Education & Reference > Science & Nature",
        ],
        "query": "chemistry coloring book for kids lab",
        "cover_rgb": ((235, 245, 235), (30, 90, 55)),
    },
    "sea-life-30": {
        "title": "Sea Life",
        "subtitle": "30 Ocean Friends to Color",
        "one_liner": "Dolphins, fish, and ocean friends — one animal per page.",
        "audience": "Kids and families who love the ocean and marine animals",
        "keywords": [
            "sea life coloring book",
            "ocean animals",
            "dolphin fish",
            "underwater coloring",
            "marine life kids",
            "coral reef",
            "ocean activity book",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Animals > Fish",
        ],
        "query": "ocean sea life coloring book for kids",
        "cover_rgb": ((220, 235, 245), (15, 70, 120)),
    },
    "space-30": {
        "title": "Space Explorers",
        "subtitle": "30 Cosmic Pages to Color",
        "one_liner": "Rockets, planets, and astronauts — one space subject per page.",
        "audience": "Kids who love rockets, planets, and exploring the stars",
        "keywords": [
            "space coloring book",
            "rockets planets",
            "astronaut kids",
            "solar system coloring",
            "outer space",
            "galaxy coloring",
            "space activity book",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Children's Books > Education & Reference > Astronomy",
        ],
        "query": "space coloring book for kids rockets planets",
        "cover_rgb": ((225, 228, 245), (40, 30, 90)),
    },
}


def ensure_meta(slug: str) -> dict:
    cfg = THEMES[slug]
    root = product_dir(slug)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pages").mkdir(exist_ok=True)
    (root / "cover").mkdir(exist_ok=True)
    (root / "art-source").mkdir(exist_ok=True)
    meta = {
        "id": slug,
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "type": "coloring-book",
        "theme": slug.replace("-30", ""),
        "trim": "letter",
        "bleed": False,
        "single_sided": True,
        "designs": 30,
        "page_count_interior": None,
        "paper_color": "white",
        "ink": "black",
        "cover_finish": "matte",
        "list_price_usd": 9.99,
        "audience": cfg["audience"],
        "one_liner": cfg["one_liner"],
        "description": (
            f"{cfg['one_liner']} Thirty original pages with bold outlines and closed shapes "
            "ready to color. Single-sided so markers stay on one design. "
            "AI-assisted artwork — disclose on KDP upload."
        ),
        "bullets": [
            "30 unique pages",
            "Bold line art with closed shapes",
            "Single-sided pages for markers",
            "8.5 x 11 inch paperback format",
            "Great for kids, families, and classrooms",
            "AI-assisted art (disclose on KDP)",
        ],
        "keywords": cfg["keywords"],
        "categories": cfg["categories"],
        "ai_assisted": True,
        "art_source": "art-source",
        "status": "draft",
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (root / "brief.md").write_text(
        f"# {cfg['title']}\n\n**Slug:** `{slug}`\n\n{cfg['one_liner']}\n",
        encoding="utf-8",
    )
    listing_dir = ROOT / "launch" / "listings"
    listing_dir.mkdir(parents=True, exist_ok=True)
    (listing_dir / f"{slug}.md").write_text(
        f"# {cfg['title']} — {cfg['subtitle']}\n\n"
        f"**Price target:** comps research\n"
        f"**AI-assisted:** Yes\n\n"
        f"## Description\n\n{meta['description']}\n",
        encoding="utf-8",
    )
    return meta


def render_cover(slug: str, page_count: int, hero_art: Path) -> Path:
    cfg = THEMES[slug]
    root = product_dir(slug)
    dims = cover_dimensions(page_count, trim="letter", paper="white")
    dpi = int(dims["dpi"])
    w, h = dims["cover_width_px"], dims["cover_height_px"]
    light, dark = cfg["cover_rgb"]
    img = Image.new("RGB", (w, h), tuple(min(255, c + 10) for c in light))
    draw = ImageDraw.Draw(img)
    bleed = float(dims["bleed_in"])
    trim_w = float(dims["trim_width_in"])
    spine = float(dims["spine_in"])
    fl = int(round((bleed + trim_w + spine) * dpi))
    ft = int(round(bleed * dpi))
    fr = int(round((bleed + trim_w + spine + trim_w) * dpi))
    fb = int(round((bleed + dims["trim_height_in"]) * dpi))
    fw, fh = fr - fl, fb - ft
    draw.rectangle((fl, ft, fr, fb), fill=light)
    draw.rectangle((int(bleed * dpi), ft, int((bleed + trim_w) * dpi), fb), fill=tuple(max(0, c - 8) for c in light))

    art = Image.open(hero_art)
    fitted = ImageOps.contain(art, (fw - 100, int(fh * 0.62)), Image.Resampling.LANCZOS)
    g = ImageEnhance.Contrast(fitted.convert("L")).enhance(1.6)
    rgb = ImageOps.colorize(g, black=dark, white=light)
    img.paste(rgb, (fl + (fw - rgb.width) // 2, ft + int(fh * 0.05)))

    band_top = ft + int(fh * 0.72)
    draw.rectangle((fl, band_top, fr, fb), fill=dark)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
        font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
        font_s = font
    title, subtitle = cfg["title"], cfg["subtitle"]
    tw = draw.textlength(title, font=font)
    sw = draw.textlength(subtitle, font=font_s)
    draw.text((fl + (fw - tw) // 2, band_top + 30), title, fill=(250, 250, 250), font=font)
    draw.text((fl + (fw - sw) // 2, band_top + 110), subtitle, fill=(220, 230, 240), font=font_s)

    out = root / "cover" / "wrap-placeholder.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, dpi=(dpi, dpi))
    (root / "cover" / "dimensions.json").write_text(json.dumps(dims, indent=2) + "\n")
    return out


def build_slug(slug: str) -> dict:
    if slug not in THEMES:
        raise SystemExit(f"Unknown slug {slug}. Choose from: {', '.join(THEMES)}")
    ensure_meta(slug)
    root = product_dir(slug)
    art_dir = root / "art-source"
    pngs = sorted(art_dir.glob("*.png"))
    if len(pngs) < 30:
        return {"ok": False, "slug": slug, "error": f"Need 30 PNGs in {art_dir}, found {len(pngs)}"}

    # Keep only first 30 sorted for stable page order
    for extra in pngs[30:]:
        extra.unlink()
    paths = import_art_folder(art_dir, root / "pages", trim="letter")
    # Trim to 30 designs if more slipped in
    for p in sorted((root / "pages").glob("page-*.png"))[30:]:
        p.unlink()
    paths = sorted((root / "pages").glob("page-*.png"))[:30]

    result = build_interior_pdf(paths, root / "interior.pdf", trim="letter", single_sided=True)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    meta["page_count_interior"] = result["page_count"]
    meta["designs"] = len(paths)
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    hero = sorted(art_dir.glob("*.png"))[0]
    render_cover(slug, result["page_count"], hero)
    research_and_price(slug, query=THEMES[slug]["query"], apply=True, allow_demo=True)
    errors = validate_product(slug)
    pkg = build_publish_package(slug) if not errors else {"ok": False, "errors": errors}
    return {
        "ok": not errors and pkg.get("ok"),
        "slug": slug,
        "pages": len(paths),
        "validation": errors,
        "publish": pkg.get("package_dir"),
    }


if __name__ == "__main__":
    slugs = sys.argv[1:] or list(THEMES)
    for slug in slugs:
        print(json.dumps(build_slug(slug), indent=2))
