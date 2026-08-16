"""Simple placeholder cover wrap for draft SKUs (replace before upload)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .build import cover_dimensions


def render_placeholder_cover(
    out_path: Path,
    *,
    title: str,
    subtitle: str,
    page_count: int,
    trim: str = "letter",
    paper: str = "white",
) -> dict:
    dims = cover_dimensions(page_count, trim=trim, paper=paper)
    dpi = int(dims["dpi"])
    w, h = dims["cover_width_px"], dims["cover_height_px"]
    img = Image.new("RGB", (w, h), (232, 236, 228))
    draw = ImageDraw.Draw(img)

    bleed = float(dims["bleed_in"])
    trim_w = float(dims["trim_width_in"])
    spine = float(dims["spine_in"])

    # Front panel starts after bleed + back + spine
    front_left = int(round((bleed + trim_w + spine) * dpi))
    front_top = int(round(bleed * dpi))
    front_right = int(round((bleed + trim_w + spine + trim_w) * dpi))
    front_bottom = int(round((bleed + dims["trim_height_in"]) * dpi))

    # Soft front panel
    draw.rectangle((front_left, front_top, front_right, front_bottom), fill=(245, 248, 242))

    # Decorative rings on front
    cx = (front_left + front_right) // 2
    cy = front_top + int((front_bottom - front_top) * 0.42)
    for r in range(80, 520, 55):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(40, 55, 45), width=3)

    font = ImageFont.load_default()
    title_y = front_top + int((front_bottom - front_top) * 0.72)
    draw.text((cx - 60, title_y), title, fill=(25, 35, 28), font=font)
    draw.text((cx - 90, title_y + 24), subtitle, fill=(60, 75, 65), font=font)
    draw.text((cx - 70, title_y + 48), "KDP Studio draft cover", fill=(110, 120, 110), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(dpi, dpi))
    return {"path": str(out_path), **dims}
