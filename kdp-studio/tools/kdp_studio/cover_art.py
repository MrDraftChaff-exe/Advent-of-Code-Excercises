"""Simple placeholder cover wrap for draft SKUs (replace before upload)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .animals import draw_fox, draw_owl
from .build import cover_dimensions


def render_placeholder_cover(
    out_path: Path,
    *,
    title: str,
    subtitle: str,
    page_count: int,
    trim: str = "letter",
    paper: str = "white",
    theme: str = "geometry",
) -> dict:
    dims = cover_dimensions(page_count, trim=trim, paper=paper)
    dpi = int(dims["dpi"])
    w, h = dims["cover_width_px"], dims["cover_height_px"]
    forest = theme in {"forest-animals", "forest", "animals"}
    bg = (214, 224, 208) if forest else (232, 236, 228)
    front_fill = (236, 242, 230) if forest else (245, 248, 242)
    ink = (28, 48, 36) if forest else (40, 55, 45)

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    bleed = float(dims["bleed_in"])
    trim_w = float(dims["trim_width_in"])
    spine = float(dims["spine_in"])

    front_left = int(round((bleed + trim_w + spine) * dpi))
    front_top = int(round(bleed * dpi))
    front_right = int(round((bleed + trim_w + spine + trim_w) * dpi))
    front_bottom = int(round((bleed + dims["trim_height_in"]) * dpi))

    draw.rectangle((front_left, front_top, front_right, front_bottom), fill=front_fill)

    cx = (front_left + front_right) // 2
    cy = front_top + int((front_bottom - front_top) * 0.40)

    if forest:
        mask = Image.new("L", (w, h), 255)
        mdraw = ImageDraw.Draw(mask)
        draw_fox(mdraw, cx - 60, cy + 30, scale=1.25, seed=1)
        draw_owl(mdraw, cx + 200, cy - 30, scale=0.7, seed=2)
        overlay = Image.new("RGB", (w, h), ink)
        img.paste(overlay, (0, 0), ImageOps.invert(mask))
    else:
        for r in range(80, 520, 55):
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=3)

    font = ImageFont.load_default()
    title_y = front_top + int((front_bottom - front_top) * 0.72)
    draw.text((cx - 70, title_y), title, fill=(20, 32, 24), font=font)
    draw.text((cx - 110, title_y + 24), subtitle, fill=(55, 72, 60), font=font)
    draw.text((cx - 80, title_y + 48), "KDP Studio draft cover", fill=(100, 115, 105), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(dpi, dpi))
    return {"path": str(out_path), **dims}
