#!/usr/bin/env python3
"""Generate a card-frame SVG from layout.json + design params.

Locked regions always come from layout.json. Design params only affect style.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
DEFAULT_LAYOUT = ROOT / "layout.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "frame"


def jagged_side_path(
    x_outer: float,
    x_inner: float,
    y0: float,
    y1: float,
    *,
    outward_left: bool,
    spikes: int = 14,
) -> str:
    """Build a jagged vertical border polygon."""
    h = y1 - y0
    pts: list[tuple[float, float]] = []
    # Outer jagged edge top -> bottom
    for i in range(spikes + 1):
        t = i / spikes
        y = y0 + h * t
        jag = 10 + (8 if i % 2 else 0)
        if outward_left:
            x = x_outer - jag if i % 2 else x_outer
        else:
            x = x_outer + jag if i % 2 else x_outer
        pts.append((x, y))
    # Inner edge bottom -> top
    pts.append((x_inner, y1))
    pts.append((x_inner, y0))
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


def flame_path(cx: float, cy: float, scale: float = 1.0) -> str:
    """Simple stylized flame silhouette centered at (cx, cy)."""
    s = scale
    return (
        f"M {cx:.1f},{cy - 22 * s:.1f} "
        f"C {cx + 8 * s:.1f},{cy - 8 * s:.1f} {cx + 16 * s:.1f},{cy + 2 * s:.1f} "
        f"{cx + 10 * s:.1f},{cy + 14 * s:.1f} "
        f"C {cx + 6 * s:.1f},{cy + 20 * s:.1f} {cx + 1 * s:.1f},{cy + 22 * s:.1f} "
        f"{cx:.1f},{cy + 18 * s:.1f} "
        f"C {cx - 1 * s:.1f},{cy + 22 * s:.1f} {cx - 6 * s:.1f},{cy + 20 * s:.1f} "
        f"{cx - 10 * s:.1f},{cy + 14 * s:.1f} "
        f"C {cx - 16 * s:.1f},{cy + 2 * s:.1f} {cx - 8 * s:.1f},{cy - 8 * s:.1f} "
        f"{cx:.1f},{cy - 22 * s:.1f} Z"
    )


def panel_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str, sw: float = 3) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" ry="4" '
        f'fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="{sw}"/>'
    )


def gradient_defs(palette: dict[str, str]) -> str:
    primary = palette.get("primary", "#F5A623")
    secondary = palette.get("secondary", "#E85D04")
    accent = palette.get("accent", "#FFED4A")
    glow = palette.get("glow", accent)
    return f"""
  <defs>
    <linearGradient id="sideFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{escape(accent)}"/>
      <stop offset="45%" stop-color="{escape(primary)}"/>
      <stop offset="100%" stop-color="{escape(secondary)}"/>
    </linearGradient>
    <radialGradient id="crestGlow" cx="50%" cy="45%" r="60%">
      <stop offset="0%" stop-color="{escape(glow)}"/>
      <stop offset="70%" stop-color="{escape(primary)}"/>
      <stop offset="100%" stop-color="{escape(secondary)}"/>
    </radialGradient>
    <linearGradient id="borderRock" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1a1a1a"/>
      <stop offset="50%" stop-color="{escape(palette.get('border', '#2A2A2A'))}"/>
      <stop offset="100%" stop-color="#111111"/>
    </linearGradient>
  </defs>
"""


def build_svg(layout: dict[str, Any], params: dict[str, Any], *, guide: bool = False) -> str:
    canvas = layout["canvas"]
    w, h = canvas["width"], canvas["height"]
    regions = layout["preserved_regions"]
    title = regions["title_box"]
    art = regions["art_window"]
    bl = regions["bottom_left_box"]
    br = regions["bottom_right_box"]

    palette = params.get("palette") or {}
    panel = palette.get("panel", "#3A3A3A")
    panel_stroke = palette.get("panel_stroke", "#F48C06")
    border = palette.get("border", "#2A2A2A")
    border_style = params.get("border_style", "jagged")

    left_outer, left_inner = 18.0, float(art["x"])
    right_inner, right_outer = float(art["x"] + art["width"]), w - 18.0

    if border_style == "jagged":
        left_path = jagged_side_path(left_outer, left_inner, 40, h - 40, outward_left=True)
        right_path = jagged_side_path(right_outer, right_inner, 40, h - 40, outward_left=False)
    else:
        left_path = f"M {left_outer},40 L {left_inner},40 L {left_inner},{h-40} L {left_outer},{h-40} Z"
        right_path = f"M {right_inner},40 L {right_outer},40 L {right_outer},{h-40} L {right_inner},{h-40} Z"

    # Top and bottom frame bands (around locked panels, not over them)
    top_band_y2 = title["y"] + title["height"] + 12
    bottom_band_y1 = bl["y"] - 20

    # Bottom center peak between boxes
    mid_x = (bl["x"] + bl["width"] + br["x"]) / 2
    peak_top = bl["y"] - 55
    peak = (
        f"M {bl['x'] + bl['width'] + 4},{bl['y'] + bl['height']} "
        f"L {bl['x'] + bl['width'] + 4},{bl['y'] - 8} "
        f"L {mid_x},{peak_top} "
        f"L {br['x'] - 4},{bl['y'] - 8} "
        f"L {br['x'] - 4},{bl['y'] + bl['height']} Z"
    )

    crest_top = flame_path(w / 2, title["y"] - 8, 0.95)
    crest_bot = flame_path(mid_x, peak_top + 28, 1.15)

    title_label = escape(str(params.get("theme", "frame")).upper())
    meta = escape(params.get("id", "frame"))

    guide_layer = ""
    if guide:
        guide_layer = f"""
  <g id="layout-guide" opacity="0.85">
    <rect x="{title['x']}" y="{title['y']}" width="{title['width']}" height="{title['height']}"
          fill="none" stroke="#00E5FF" stroke-width="2" stroke-dasharray="6 4"/>
    <rect x="{art['x']}" y="{art['y']}" width="{art['width']}" height="{art['height']}"
          fill="none" stroke="#39FF14" stroke-width="2" stroke-dasharray="6 4"/>
    <rect x="{bl['x']}" y="{bl['y']}" width="{bl['width']}" height="{bl['height']}"
          fill="none" stroke="#FF4D6D" stroke-width="2" stroke-dasharray="6 4"/>
    <rect x="{br['x']}" y="{br['y']}" width="{br['width']}" height="{br['height']}"
          fill="none" stroke="#FF4D6D" stroke-width="2" stroke-dasharray="6 4"/>
    <text x="{title['x'] + 8}" y="{title['y'] + 18}" fill="#00E5FF" font-size="14" font-family="monospace">title_box</text>
    <text x="{art['x'] + 8}" y="{art['y'] + 22}" fill="#39FF14" font-size="14" font-family="monospace">art_window</text>
    <text x="{bl['x'] + 8}" y="{bl['y'] + 18}" fill="#FF4D6D" font-size="14" font-family="monospace">bottom_left_box</text>
    <text x="{br['x'] + 8}" y="{br['y'] + 18}" fill="#FF4D6D" font-size="14" font-family="monospace">bottom_right_box</text>
  </g>
"""

    # Checkerboard only in guide mode to show transparency; otherwise fully transparent hole
    art_bg = ""
    if guide:
        art_bg = f"""
  <pattern id="checker" width="20" height="20" patternUnits="userSpaceOnUse">
    <rect width="10" height="10" fill="#ddd"/>
    <rect x="10" y="10" width="10" height="10" fill="#ddd"/>
    <rect x="10" width="10" height="10" fill="#bbb"/>
    <rect y="10" width="10" height="10" fill="#bbb"/>
  </pattern>
  <rect x="{art['x']}" y="{art['y']}" width="{art['width']}" height="{art['height']}" fill="url(#checker)"/>
"""

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <!-- generated frame: {meta} | layout: {escape(layout.get('name', 'layout'))} -->
  {gradient_defs(palette)}
  <!-- outer void stays transparent except frame chrome -->
  <rect x="0" y="0" width="{w}" height="{h}" fill="none"/>

  <!-- top frame band -->
  <path d="M 40,20 L {w-40},20 L {w-55},{top_band_y2} L 55,{top_band_y2} Z"
        fill="url(#borderRock)" stroke="{escape(border)}" stroke-width="2"/>

  <!-- bottom frame band -->
  <path d="M 55,{bottom_band_y1} L {w-55},{bottom_band_y1} L {w-40},{h-20} L 40,{h-20} Z"
        fill="url(#borderRock)" stroke="{escape(border)}" stroke-width="2"/>

  <!-- side borders -->
  <path d="{left_path}" fill="url(#sideFill)" stroke="{escape(border)}" stroke-width="2"/>
  <path d="{right_path}" fill="url(#sideFill)" stroke="{escape(border)}" stroke-width="2"/>

  <!-- bottom center peak -->
  <path d="{peak}" fill="url(#borderRock)" stroke="{escape(border)}" stroke-width="2"/>

  <!-- crests -->
  <path d="{crest_top}" fill="url(#crestGlow)" stroke="{escape(panel_stroke)}" stroke-width="1.5"/>
  <path d="{crest_bot}" fill="url(#crestGlow)" stroke="{escape(panel_stroke)}" stroke-width="1.5"/>

  <!-- locked panels (positions from layout.json) -->
  {panel_rect(title['x'], title['y'], title['width'], title['height'], panel, panel_stroke)}
  {panel_rect(bl['x'], bl['y'], bl['width'], bl['height'], panel, panel_stroke)}
  {panel_rect(br['x'], br['y'], br['width'], br['height'], panel, panel_stroke)}

  <!-- art window: intentional hole (transparent) -->
  {art_bg}
  <rect x="{art['x']}" y="{art['y']}" width="{art['width']}" height="{art['height']}"
        fill="none" stroke="{escape(panel_stroke)}" stroke-width="2" opacity="0.35"/>

  <!-- subtle labels for empty panels (optional visual cue, not locked content) -->
  <text x="{title['x'] + title['width']/2}" y="{title['y'] + title['height']/2 + 5}"
        text-anchor="middle" fill="{escape(panel_stroke)}" opacity="0.35"
        font-family="Georgia, serif" font-size="18">{title_label}</text>

  {guide_layer}
</svg>
'''
    return svg


def validate_params_against_layout(params: dict[str, Any]) -> None:
    """Ensure callers did not try to move locked regions via params."""
    forbidden = {"x", "y", "width", "height", "title_box", "art_window", "bottom_left_box", "bottom_right_box"}
    overlap = forbidden.intersection(params.keys())
    if overlap:
        raise SystemExit(
            f"Design params must not override layout geometry. Remove keys: {sorted(overlap)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, required=True, help="Path to design params JSON")
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT, help="Path to layout.json")
    parser.add_argument("--out", type=Path, help="Output SVG path (default: samples/<id>.svg)")
    parser.add_argument("--guide", action="store_true", help="Draw locked-region overlay guides")
    args = parser.parse_args()

    layout = load_json(args.layout)
    params = load_json(args.params)
    validate_params_against_layout(params)

    frame_id = slugify(params.get("id") or params.get("theme") or "frame")
    out = args.out or (ROOT / "samples" / f"{frame_id}{'-guide' if args.guide else ''}.svg")
    out.parent.mkdir(parents=True, exist_ok=True)

    svg = build_svg(layout, params, guide=args.guide)
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
