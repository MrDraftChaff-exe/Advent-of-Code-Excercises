#!/usr/bin/env python3
"""Build image-generation prompts and post-process HQ card frames.

Crude programmatic SVG chrome is not the production look. Final frames are
high-quality illustrated assets whose content slots match layout.json.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parent
DEFAULT_LAYOUT = ROOT / "layout.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "frame"


def build_prompt(layout: dict[str, Any], params: dict[str, Any]) -> str:
    """Compose a strict layout + rich art direction prompt."""
    c = layout["canvas"]
    r = layout["preserved_regions"]
    title, art, bl, br = r["title_box"], r["art_window"], r["bottom_left_box"], r["bottom_right_box"]
    palette = params.get("palette") or {}
    materials = params.get("materials") or {}
    crest = params.get("crest") or {}

    colors = ", ".join(f"{k} {v}" for k, v in palette.items() if v)
    mat = ", ".join(f"{k}: {v}" for k, v in materials.items() if v)

    return f"""
High-end fantasy TCG card FRAME TEMPLATE, vertical portrait {c['width']}x{c['height']} (5:7), premium game UI asset quality.

LOCKED LAYOUT — match these slots exactly; do not move or resize them:
1) TOP TITLE BANNER: empty horizontal plaque at x={title['x']} y={title['y']} size {title['width']}x{title['height']}, centered under a small crest.
2) CENTER ART WINDOW: large CLEAR TRANSPARENT rectangle at x={art['x']} y={art['y']} size {art['width']}x{art['height']}. No artwork, no texture, no gradient inside — empty hole only.
3) BOTTOM LEFT BANNER: empty plaque at x={bl['x']} y={bl['y']} size {bl['width']}x{bl['height']}.
4) BOTTOM RIGHT BANNER: empty plaque at x={br['x']} y={br['y']} size {br['width']}x{br['height']}.
5) Small crest/ornament allowed between the two bottom banners only.

THEME: {params.get('theme', 'fantasy')} / mood: {params.get('mood', 'polished')} / element: {params.get('element', '')}
PALETTE: {colors or 'cohesive premium palette'}
MATERIALS: {mat or 'rich detailed materials with soft shading'}
BORDER STYLE: {params.get('border_style', 'ornate')}
SIDE FILL / ORNAMENTS: {params.get('side_fill', '')}; {', '.join(params.get('ornaments') or [])}
CREST MOTIF: {crest.get('motif', 'thematic emblem')} at top center and bottom center.
TITLE BOX STYLE: {params.get('title_box_style', 'empty ornate plaque, no text')}
FOOTER BOX STYLE: {params.get('footer_box_style', 'matching empty plaques, no text')}
{params.get('prompt_extras', '')}

QUALITY BAR: clean digital illustration / polished vector-painted game asset — crisp edges, soft realistic shading, fine material detail (wood grain, metal rivets, petals, glow), NOT flat UI shapes, NOT simple gradients, NOT low-poly, NOT pixel art, NOT muddy, NOT blurry.
No readable text, no letters, no watermark, no character art in the center hole.
Full-bleed decorative frame on transparent or plain backdrop; center remains an empty opening.
""".strip()


def punch_art_hole(image: Image.Image, layout: dict[str, Any], *, inset: int = 0) -> Image.Image:
    """Make the art-window interior transparent while preserving a framed bezel.

    Prefer clearing empty fill (white / magenta / near-black flat fill) inside the
    locked art rect. A hard rect punch is used as fallback for remaining opaque
    interior pixels, optionally inset so an illustrated rim can survive.
    """
    art = layout["preserved_regions"]["art_window"]
    canvas = layout["canvas"]
    img = image.convert("RGBA").resize((canvas["width"], canvas["height"]), Image.Resampling.LANCZOS)
    pixels = img.load()
    x0, y0 = art["x"] + inset, art["y"] + inset
    x1, y1 = art["x"] + art["width"] - inset, art["y"] + art["height"] - inset

    def is_empty_fill(r: int, g: int, b: int, a: int) -> bool:
        if a < 16:
            return True
        # pure / near white
        if r > 245 and g > 245 and b > 245:
            return True
        # layout magenta guide
        if r > 230 and g < 40 and b > 230:
            return True
        # flat near-black placeholder (not textured rock)
        if r < 28 and g < 28 and b < 28:
            return True
        return False

    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = pixels[x, y]
            if is_empty_fill(r, g, b, a):
                pixels[x, y] = (0, 0, 0, 0)
            else:
                # hard-clear remaining interior so art can composite cleanly;
                # bezel lives outside inset / outside empty-fill regions
                pixels[x, y] = (0, 0, 0, 0)
    return img


def make_preview_with_checker(image: Image.Image, layout: dict[str, Any], cell: int = 16) -> Image.Image:
    """Composite transparent frame over a checkerboard for previewing."""
    w, h = image.size
    preview = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            c = (210, 210, 210, 255) if ((x // cell) + (y // cell)) % 2 == 0 else (160, 160, 160, 255)
            for yy in range(y, min(y + cell, h)):
                for xx in range(x, min(x + cell, w)):
                    preview.putpixel((xx, yy), c)
    return Image.alpha_composite(preview, image.convert("RGBA"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--print-prompt", action="store_true")
    parser.add_argument("--punch", type=Path, help="Input PNG/WebP to punch art hole into")
    parser.add_argument("--out", type=Path, help="Output path for punched PNG")
    parser.add_argument("--inset", type=int, default=0, help="Keep N px of art-window rim when punching")
    args = parser.parse_args()

    layout = load_json(args.layout)
    params = load_json(args.params)
    prompt = build_prompt(layout, params)

    if args.print_prompt:
        print(prompt)

    if args.punch:
        frame_id = slugify(params.get("id") or "frame")
        out = args.out or (ROOT / "samples" / f"{frame_id}.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        punched = punch_art_hole(Image.open(args.punch), layout, inset=args.inset)
        punched.save(out)
        print(f"Wrote {out}")
        if args.preview:
            prev = out.with_name(out.stem + "-preview.png")
            make_preview_with_checker(punched, layout).save(prev)
            print(f"Wrote {prev}")


if __name__ == "__main__":
    main()
