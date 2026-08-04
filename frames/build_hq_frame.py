#!/usr/bin/env python3
"""Build image-generation prompts and post-process HQ card frames.

Crude programmatic SVG chrome is not the production look. Final frames are
high-quality illustrated assets whose content slots match layout.json.

Layering rule: gray content boxing sits UNDER the frame so ornate bezel /
ornament details are never covered or punched away.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
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

CRITICAL LAYERING: The decorative frame, bezels, rivets, crests, and ornaments must OVERLAY the content slots. Gray/empty boxing is behind the frame; never cover or crop away inner frame details.

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


def _to_canvas(image: Image.Image, layout: dict[str, Any]) -> np.ndarray:
    canvas = layout["canvas"]
    img = image.convert("RGBA").resize((canvas["width"], canvas["height"]), Image.Resampling.LANCZOS)
    return np.array(img)


def punch_art_hole(
    image: Image.Image,
    layout: dict[str, Any],
    *,
    inset: int = 0,
    preserve_frame_detail: bool = True,
) -> Image.Image:
    """Clear empty art fill via flood-fill so frame bezels stay opaque on top.

    Only near-white / magenta / already-clear pixels are removable. Dark metal,
    stone, glow, and ornament pixels are preserved so gray boxing can sit under
    the frame without eating details.
    """
    from collections import deque

    art = layout["preserved_regions"]["art_window"]
    arr = _to_canvas(image, layout)
    h, w = arr.shape[:2]
    pad = max(inset, 1)
    x0, y0 = art["x"] + pad, art["y"] + pad
    x1, y1 = art["x"] + art["width"] - pad, art["y"] + art["height"] - pad

    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    a = arr[:, :, 3]
    lum = (r + g + b) / 3.0
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    # Never treat dark metal / textured chrome as empty.
    passable = ((lum > 185) & (sat < 50)) | ((r > 220) & (g < 60) & (b > 220)) | (a < 16)
    if not preserve_frame_detail:
        # Unsafe mode used only for debugging: allow clearing flat near-black too.
        passable = passable | ((lum < 26) & (sat < 12) & (a > 0))

    allowed = np.zeros((h, w), dtype=bool)
    allowed[y0:y1, x0:x1] = True
    seed_mask = passable & allowed

    visited = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for yy in range(y0 + 10, y1 - 10, 40):
        for xx in range(x0 + 10, x1 - 10, 40):
            if seed_mask[yy, xx]:
                visited[yy, xx] = True
                q.append((xx, yy))
    for yy in range(max(y0, y1 - 90), y1 - 1, 8):
        for xx in range(x0 + 8, x1 - 8, 16):
            if seed_mask[yy, xx] and not visited[yy, xx]:
                visited[yy, xx] = True
                q.append((xx, yy))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and seed_mask[ny, nx]:
                visited[ny, nx] = True
                q.append((nx, ny))

    arr[visited] = (0, 0, 0, 0)

    # Sweep leftover disconnected near-white islands inside the art rect only.
    pale = ((lum > 200) & (sat < 40) & (a > 0))
    pale_art = np.zeros((h, w), dtype=bool)
    pale_art[y0:y1, x0:x1] = pale[y0:y1, x0:x1]
    arr[pale_art] = (0, 0, 0, 0)
    return Image.fromarray(arr, "RGBA")


def make_slot_underlay(layout: dict[str, Any], *, cell: int = 16, full_checker: bool = True) -> Image.Image:
    """Gray boxing for locked slots — drawn UNDER the frame.

    full_checker=True makes the entire canvas checkerboard so exterior
    transparency of a frame cutout is obvious.
    """
    c = layout["canvas"]
    w, h = c["width"], c["height"]
    under = np.zeros((h, w, 4), dtype=np.uint8)

    yy, xx = np.indices((h, w))
    checker = ((xx // cell) + (yy // cell)) % 2 == 0
    if full_checker:
        under[checker] = (186, 186, 186, 255)
        under[~checker] = (128, 128, 128, 255)
    else:
        under[:, :] = (24, 24, 28, 255)
        art = layout["preserved_regions"]["art_window"]
        ay, ax = art["height"], art["width"]
        yy2, xx2 = np.indices((ay, ax))
        art_checker = ((xx2 // cell) + (yy2 // cell)) % 2 == 0
        art_block = np.zeros((ay, ax, 4), dtype=np.uint8)
        art_block[art_checker] = (186, 186, 186, 255)
        art_block[~art_checker] = (128, 128, 128, 255)
        under[art["y"] : art["y"] + ay, art["x"] : art["x"] + ax] = art_block

    # Slightly darker plaque underlays so empty plaque faces still read as slots.
    for key in ("title_box", "bottom_left_box", "bottom_right_box"):
        box = layout["preserved_regions"][key]
        under[
            box["y"] : box["y"] + box["height"],
            box["x"] : box["x"] + box["width"],
        ] = (96, 96, 102, 255)

    return Image.fromarray(under, "RGBA")


def make_preview_with_checker(image: Image.Image, layout: dict[str, Any], cell: int = 16) -> Image.Image:
    """Gray boxing underlay, then frame on top so details are not missed."""
    under = make_slot_underlay(layout, cell=cell)
    frame = image.convert("RGBA")
    if frame.size != under.size:
        canvas = layout["canvas"]
        frame = frame.resize((canvas["width"], canvas["height"]), Image.Resampling.LANCZOS)
    return Image.alpha_composite(under, frame)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--print-prompt", action="store_true")
    parser.add_argument("--punch", type=Path, help="Input PNG/WebP to punch art hole into")
    parser.add_argument("--out", type=Path, help="Output path for punched PNG")
    parser.add_argument(
        "--inset",
        type=int,
        default=0,
        help="Optional margin inside art rect when searching for empty fill",
    )
    parser.add_argument(
        "--hard-clear-interior",
        action="store_true",
        help="Unsafe: also wipe non-empty pixels inside art rect (can destroy bezel details)",
    )
    parser.add_argument("--preview", action="store_true", help="Also write checkerboard preview")
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
        punched = punch_art_hole(
            Image.open(args.punch),
            layout,
            inset=args.inset,
            preserve_frame_detail=not args.hard_clear_interior,
        )
        punched.save(out)
        print(f"Wrote {out}")
        if args.preview:
            prev = out.with_name(out.stem + "-preview.png")
            make_preview_with_checker(punched, layout).save(prev)
            print(f"Wrote {prev}")


if __name__ == "__main__":
    main()
