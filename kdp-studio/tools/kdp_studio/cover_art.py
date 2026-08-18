"""KDP paperback cover wrap renderer — front, spine, and back."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from .build import cover_dimensions

FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"

# House pen name for KDP author field + cover byline
PEN_NAME = "Elsie Wren"

# Typography:
# - Lilita One — chunky display with character (replaces generic Fredoka)
# - Source Sans 3 — clean subtitle/body that stays readable at small sizes
# - Patrick Hand — warm handwritten byline for the pen name
TITLE_FONT = "LilitaOne-Regular.ttf"
SUB_FONT = "SourceSans3-SemiBold.ttf"
TAG_FONT = "SourceSans3-SemiBold.ttf"
AUTHOR_FONT = "PatrickHand-Regular.ttf"
BODY_FONT = "SourceSans3-Regular.ttf"

# KDP overlays a free EAN-13 on the back if we leave this well empty.
# Official size ~2.0" × 1.2", ≥0.25" from spine and trim.
BARCODE_W_IN = 2.0
BARCODE_H_IN = 1.2
BARCODE_MARGIN_IN = 0.25

# Theme palettes — all titles share STYLE.md bold-and-easy art.
# Each book gets its own hero crop, back motif, headline, and bullets.
THEMES: dict[str, dict] = {
    "quiet-places-40": {
        "gradient": ((190, 220, 200), (55, 100, 75)),
        "back_fill": ((210, 228, 214), (72, 112, 88)),
        "accent": (255, 210, 130),
        "title": (255, 255, 255),
        "stroke": (30, 60, 40),
        "hero": "cover-hero-quiet.png",
        "hero_center": (0.52, 0.38),
        "back_label": "Breathe and color",
        "motif": "leaves",
        "theme_bullet": "Calm scenes for stress relief",
        "chips": [(86, 148, 108), (255, 210, 130), (236, 244, 232)],
        "designs": 40,
    },
    "stained-glass-40": {
        "gradient": ((210, 195, 240), (80, 45, 120)),
        "back_fill": ((186, 160, 220), (72, 38, 108)),
        "accent": (255, 200, 120),
        "title": (255, 255, 255),
        "stroke": (40, 20, 70),
        "hero": "cover-hero-stained-glass.png",
        "hero_center": (0.50, 0.50),
        "back_label": "Color the light",
        "motif": "glass",
        "theme_bullet": "Windows, roses, and jewel panes",
        "chips": [(196, 48, 72), (236, 190, 72), (48, 78, 168)],
        "designs": 40,
    },
    "cars-40": {
        "gradient": ((180, 210, 245), (30, 70, 130)),
        "back_fill": ((120, 170, 210), (28, 62, 118)),
        "accent": (255, 180, 70),
        "title": (255, 255, 255),
        "stroke": (20, 40, 80),
        "hero": "cover-hero-cars.png",
        "hero_center": (0.42, 0.58),
        "back_label": "Hit the road",
        "motif": "road",
        "theme_bullet": "Cars, trucks, and road trips",
        "chips": [(196, 48, 48), (42, 92, 168), (255, 176, 64)],
        "designs": 40,
    },
    "planes-40": {
        "gradient": ((190, 220, 245), (40, 90, 150)),
        "back_fill": ((150, 195, 230), (36, 82, 140)),
        "accent": (255, 200, 90),
        "title": (255, 255, 255),
        "stroke": (20, 50, 90),
        "hero": "cover-hero-planes.png",
        "hero_center": (0.48, 0.40),
        "back_label": "Up in the clouds",
        "motif": "clouds",
        "theme_bullet": "Airplanes and sky adventures",
        "chips": [(72, 148, 214), (244, 248, 252), (28, 64, 128)],
        "designs": 40,
    },
    "buildings-40": {
        "gradient": ((230, 220, 210), (90, 70, 55)),
        "back_fill": ((214, 196, 176), (86, 62, 46)),
        "accent": (255, 190, 120),
        "title": (255, 255, 255),
        "stroke": (50, 35, 25),
        "hero": "cover-hero-buildings.png",
        "hero_center": (0.55, 0.36),
        "back_label": "Color the skyline",
        "motif": "skyline",
        "theme_bullet": "Cottages, shops, and castles",
        "chips": [(176, 92, 64), (236, 214, 186), (92, 64, 48)],
        "designs": 40,
    },
    "food-40": {
        "gradient": ((255, 230, 210), (170, 80, 55)),
        "back_fill": ((242, 196, 164), (156, 68, 46)),
        "accent": (255, 210, 100),
        "title": (255, 255, 255),
        "stroke": (90, 40, 25),
        "hero": "cover-hero-food.png",
        "hero_center": (0.50, 0.48),
        "back_label": "Dig in and color",
        "motif": "picnic",
        "theme_bullet": "Meals, desserts, and picnics",
        "chips": [(204, 68, 48), (86, 148, 72), (255, 210, 100)],
        "designs": 40,
    },
    "mountains-40": {
        "gradient": ((200, 225, 235), (50, 80, 105)),
        "back_fill": ((168, 198, 214), (44, 72, 96)),
        "accent": (255, 200, 120),
        "title": (255, 255, 255),
        "stroke": (25, 45, 60),
        "hero": "cover-hero-mountains.png",
        "hero_center": (0.50, 0.32),
        "back_label": "Reach the summit",
        "motif": "peaks",
        "theme_bullet": "Peaks, trails, and alpine views",
        "chips": [(90, 150, 186), (52, 92, 72), (244, 248, 250)],
        "designs": 40,
    },
}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = FONTS / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    # Fallbacks
    for alt in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(alt, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
    return base.resize((w, h), Image.Resampling.BILINEAR)


def _fit_cover(
    src: Image.Image,
    box: tuple[int, int],
    centering: tuple[float, float] = (0.5, 0.42),
) -> Image.Image:
    """Cover-fit (fill) into box, cropped around centering."""
    return ImageOps.fit(src.convert("RGB"), box, method=Image.Resampling.LANCZOS, centering=centering)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _draw_text_outlined(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    stroke: tuple[int, int, int],
    stroke_width: int,
) -> None:
    draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke)


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if _text_size(draw, trial, font)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text]


def _draw_soft_vignette(img: Image.Image, panel: tuple[int, int, int, int], strength: float = 0.35) -> None:
    """Darken top of front panel so white title stays readable."""
    fl, ft, fr, fb = panel
    fw, fh = fr - fl, fb - ft
    veil = Image.new("L", (fw, fh), 0)
    vdraw = ImageDraw.Draw(veil)
    band = int(fh * 0.38)
    for y in range(band):
        alpha = int(255 * strength * (1 - y / max(1, band - 1)))
        vdraw.line([(0, y), (fw, y)], fill=alpha)
    dark = Image.new("RGB", (fw, fh), (10, 20, 30))
    panel_img = img.crop((fl, ft, fr, fb))
    panel_img = Image.composite(dark, panel_img, veil)
    img.paste(panel_img, (fl, ft))


def _motif_ink(theme: dict) -> tuple[int, int, int]:
    acc = tuple(theme["accent"])
    return tuple(int(acc[i] * 0.42 + 255 * 0.58) for i in range(3))


def _draw_motif_at(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    motif: str,
    ink: tuple[int, int, int],
    scale: int = 110,
) -> None:
    s = scale

    def oval(ox: int, oy: int, rx: int, ry: int, width: int = 5) -> None:
        draw.ellipse((ox - rx, oy - ry, ox + rx, oy + ry), outline=ink, width=width)

    if motif == "leaves":
        oval(cx, cy, int(s * 0.72), int(s * 0.42), 6)
        draw.arc((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 8), 200, 340, fill=ink, width=5)
        draw.line((cx, cy - s // 5, cx, cy + s // 3), fill=ink, width=4)
    elif motif == "glass":
        pts = [
            (cx, cy - s),
            (cx + int(s * 0.78), cy - s // 5),
            (cx + int(s * 0.48), cy + s),
            (cx - int(s * 0.48), cy + s),
            (cx - int(s * 0.78), cy - s // 5),
        ]
        draw.polygon(pts, outline=ink)
        draw.line((cx, cy - s, cx, cy + s), fill=ink, width=4)
        draw.line((cx - int(s * 0.5), cy, cx + int(s * 0.5), cy), fill=ink, width=3)
    elif motif == "road":
        draw.rounded_rectangle((cx - s, cy - 18, cx + s, cy + 18), radius=10, outline=ink, width=5)
        draw.line((cx - 28, cy, cx - 8, cy), fill=ink, width=4)
        draw.line((cx + 8, cy, cx + 28, cy), fill=ink, width=4)
        oval(cx - int(s * 0.55), cy + 28, 16, 16, 4)
        oval(cx + int(s * 0.55), cy + 28, 16, 16, 4)
    elif motif == "clouds":
        oval(cx, cy, s, s // 2, 5)
        oval(cx - s // 2, cy + 10, s // 2, s // 3, 4)
        oval(cx + s // 2, cy + 8, int(s * 0.55), s // 3, 4)
        draw.line((cx - int(s * 0.35), cy + s // 2 + 8, cx + int(s * 0.55), cy + s // 2 + 8), fill=ink, width=4)
    elif motif == "skyline":
        x = cx - int(s * 1.15)
        for ht, ww in ((int(s * 0.7), 28), (s, 32), (int(s * 0.55), 26), (int(s * 0.88), 30)):
            draw.rectangle((x, cy + 20 - ht, x + ww, cy + 28), outline=ink, width=4)
            draw.rectangle((x + 7, cy + 28 - ht + 10, x + 15, cy + 28 - ht + 22), outline=ink, width=3)
            x += ww + 8
    elif motif == "picnic":
        oval(cx, cy, int(s * 0.55), int(s * 0.55), 5)
        oval(cx, cy, int(s * 0.28), int(s * 0.28), 4)
        draw.arc((cx - int(s * 0.7), cy - 8, cx + int(s * 0.7), cy + int(s * 0.85)), 200, 340, fill=ink, width=5)
        draw.line((cx + int(s * 0.15), cy - int(s * 0.7), cx + int(s * 0.15), cy - int(s * 0.2)), fill=ink, width=4)
    else:  # peaks
        draw.polygon(
            [(cx - int(s * 0.95), cy + int(s * 0.45)), (cx, cy - s), (cx + int(s * 0.95), cy + int(s * 0.45))],
            outline=ink,
        )
        draw.polygon(
            [(cx + int(s * 0.15), cy + int(s * 0.45)), (cx + int(s * 0.7), cy - int(s * 0.35)), (cx + int(s * 1.2), cy + int(s * 0.45))],
            outline=ink,
        )


def _back_motif(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    theme: dict,
    forbidden: tuple[int, int, int, int],
) -> None:
    """Thematic doodles on the back cover — never in the barcode well."""
    l, t, r, b = box
    w, h = r - l, b - t
    motif = str(theme.get("motif", "leaves"))
    ink = _motif_ink(theme)
    fl, ft, fr, fb = forbidden

    def hits_well(cx: int, cy: int, pad: int = 140) -> bool:
        return cx + pad > fl and cx - pad < fr and cy + pad > ft and cy - pad < fb

    placements = (
        (0.16, 0.16, 120),
        (0.84, 0.15, 100),
        (0.14, 0.78, 110),
        (0.50, 0.88, 90),
    )
    for fx, fy, scale in placements:
        cx, cy = l + int(w * fx), t + int(h * fy)
        if hits_well(cx, cy, pad=scale + 20):
            continue
        _draw_motif_at(draw, cx, cy, motif, ink, scale=scale)


def _front_flourish(
    draw: ImageDraw.ImageDraw,
    panel: tuple[int, int, int, int],
    theme: dict,
) -> None:
    """Small unique doodles in the front lower corners."""
    l, t, r, b = panel
    w, h = r - l, b - t
    motif = str(theme.get("motif", "leaves"))
    ink = tuple(theme["accent"])
    _draw_motif_at(draw, l + int(w * 0.14), t + int(h * 0.88), motif, ink, scale=70)
    _draw_motif_at(draw, l + int(w * 0.86), t + int(h * 0.88), motif, ink, scale=70)


def _barcode_box(
    *,
    back_l: int,
    back_r: int,
    bottom: int,
    dpi: int,
) -> tuple[int, int, int, int]:
    """KDP barcode well: 2.0\" × 1.2\", 0.25\" left of spine and above bottom trim."""
    margin = int(round(BARCODE_MARGIN_IN * dpi))
    bc_w = int(round(BARCODE_W_IN * dpi))
    bc_h = int(round(BARCODE_H_IN * dpi))
    bc_r = back_r - margin
    bc_b = bottom - margin
    bc_l = bc_r - bc_w
    bc_t = bc_b - bc_h
    return bc_l, bc_t, bc_r, bc_b


def _draw_barcode_well(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Solid light rectangle for KDP's free EAN-13 — no text or art inside."""
    l, t, r, b = box
    draw.rounded_rectangle((l, t, r, b), radius=10, fill=(255, 255, 255), outline=(236, 236, 232), width=2)


def render_theme_cover(
    *,
    slug: str,
    title: str,
    subtitle: str,
    one_liner: str,
    page_count: int,
    hero_path: Path,
    out_path: Path,
    author: str = PEN_NAME,
    trim: str = "letter",
    paper: str = "white",
) -> dict:
    """Render a full KDP wrap with a unique front hero, spine, and thematic back."""
    theme = THEMES.get(slug, {
        "gradient": ((220, 230, 240), (60, 90, 120)),
        "back_fill": ((220, 230, 240), (60, 90, 120)),
        "accent": (255, 210, 100),
        "title": (255, 255, 255),
        "stroke": (30, 40, 60),
        "back_label": "Coloring book",
        "hero_center": (0.5, 0.42),
        "motif": "leaves",
        "theme_bullet": "Original bold-and-easy scenes",
        "chips": [(255, 210, 100), (240, 244, 248), (60, 90, 120)],
        "designs": 40,
    })
    dims = cover_dimensions(page_count, trim=trim, paper=paper)
    dpi = int(dims["dpi"])
    w, h = dims["cover_width_px"], dims["cover_height_px"]
    bleed = float(dims["bleed_in"])
    trim_w = float(dims["trim_width_in"])
    spine = float(dims["spine_in"])
    trim_h = float(dims["trim_height_in"])

    # Panel bounds (trim edges, inside bleed)
    back_l = int(round(bleed * dpi))
    back_r = int(round((bleed + trim_w) * dpi))
    spine_l = back_r
    spine_r = int(round((bleed + trim_w + spine) * dpi))
    front_l = spine_r
    front_r = int(round((bleed + trim_w + spine + trim_w) * dpi))
    top = int(round(bleed * dpi))
    bottom = int(round((bleed + trim_h) * dpi))

    top_c, bot_c = theme["gradient"]
    img = _gradient((w, h), top_c, bot_c)
    draw = ImageDraw.Draw(img)

    # --- Front: full-bleed hero ---
    hero = Image.open(hero_path).convert("RGB")
    # Brighten slightly for print punch
    hero = ImageEnhance.Color(hero).enhance(1.08)
    hero = ImageEnhance.Contrast(hero).enhance(1.05)
    front_w, front_h = front_r - front_l, bottom - top
    # Extend hero into bleed a bit past trim
    bleed_px = int(round(bleed * dpi))
    hero_box = (front_w + bleed_px, front_h + 2 * bleed_px)
    raw_c = theme.get("hero_center", (0.5, 0.42))
    centering = (float(raw_c[0]), float(raw_c[1]))
    fitted = _fit_cover(hero, hero_box, centering=centering)
    paste_x = front_l - bleed_px // 4
    paste_y = top - bleed_px
    img.paste(fitted, (paste_x, paste_y))

    # Unique back panel — theme gradient, not a copy of the front wash
    fill = theme.get("back_fill", theme["gradient"])
    back_w_early = back_r - back_l
    back_h_early = bottom - top
    back_grad = _gradient((back_w_early, back_h_early), fill[0], fill[1])
    wash = ImageOps.fit(hero, (back_w_early, back_h_early), centering=centering).filter(
        ImageFilter.GaussianBlur(28)
    )
    wash = ImageEnhance.Brightness(wash).enhance(0.72)
    wash = ImageEnhance.Color(wash).enhance(0.55)
    back_panel = Image.blend(back_grad, wash, 0.18)
    img.paste(back_panel, (back_l, top))

    # Solid spine so titles read on a shelf and each book reads as its own color
    spine_fill = tuple(theme["stroke"])
    draw = ImageDraw.Draw(img)
    draw.rectangle((spine_l, 0, spine_r, h), fill=spine_fill)

    front_panel = (front_l, top, front_r, bottom)
    _draw_soft_vignette(img, front_panel, strength=0.52)
    draw = ImageDraw.Draw(img)

    # Title block — brand-first, large, top of front
    title_font_size = 124 if len(title) < 14 else 100 if len(title) < 20 else 86
    title_font = _font(TITLE_FONT, title_font_size)
    sub_font = _font(SUB_FONT, 42)
    tag_font = _font(TAG_FONT, 32)

    # Fit title to front width with padding
    pad = int(front_w * 0.06)
    max_title_w = front_w - 2 * pad
    while title_font_size > 64 and _text_size(draw, title, title_font)[0] > max_title_w:
        title_font_size -= 4
        title_font = _font(TITLE_FONT, title_font_size)

    tw, th = _text_size(draw, title, title_font)
    title_x = front_l + (front_w - tw) // 2
    title_y = top + int(front_h * 0.055)
    _draw_text_outlined(
        draw,
        (title_x, title_y),
        title,
        font=title_font,
        fill=tuple(theme["title"]),
        stroke=tuple(theme["stroke"]),
        stroke_width=max(5, title_font_size // 16),
    )

    # Accent underline
    accent = tuple(theme["accent"])
    line_y = title_y + th + 16
    line_w = min(int(front_w * 0.32), max(tw // 2, 180))
    draw.rounded_rectangle(
        (
            front_l + (front_w - line_w) // 2,
            line_y,
            front_l + (front_w + line_w) // 2,
            line_y + 12,
        ),
        radius=6,
        fill=accent,
    )

    tag = "COLORING BOOK"
    tag_w, tag_h = _text_size(draw, tag, tag_font)
    tag_y = line_y + 28
    # White + dark stroke (accent fill fails on bright sky/sun heroes)
    _draw_text_outlined(
        draw,
        (front_l + (front_w - tag_w) // 2, tag_y),
        tag,
        font=tag_font,
        fill=(255, 255, 255),
        stroke=tuple(theme["stroke"]),
        stroke_width=2,
    )
    # Accent dots flanking the tag for color without hurting legibility
    gap = 28
    cy = tag_y + tag_h // 2
    r = 7
    left_x = front_l + (front_w - tag_w) // 2 - gap
    right_x = front_l + (front_w + tag_w) // 2 + gap
    draw.ellipse((left_x - r, cy - r, left_x + r, cy + r), fill=accent)
    draw.ellipse((right_x - r, cy - r, right_x + r, cy + r), fill=accent)

    sw, sh = _text_size(draw, subtitle, sub_font)
    sub_x = front_l + (front_w - sw) // 2
    sub_y = tag_y + tag_h + 18
    _draw_text_outlined(
        draw,
        (sub_x, sub_y),
        subtitle,
        font=sub_font,
        fill=(255, 255, 255),
        stroke=tuple(theme["stroke"]),
        stroke_width=2,
    )

    byline = f"by {author}"
    author_font = _font(AUTHOR_FONT, 56)
    aw, ah = _text_size(draw, byline, author_font)
    author_y = sub_y + sh + 26
    _draw_text_outlined(
        draw,
        (front_l + (front_w - aw) // 2, author_y),
        byline,
        font=author_font,
        fill=(255, 252, 240),
        stroke=tuple(theme["stroke"]),
        stroke_width=2,
    )
    _front_flourish(draw, front_panel, theme)

    # --- Spine ---
    spine_w = spine_r - spine_l
    if spine_w > 20:
        spine_font = _font(SUB_FONT, max(22, min(36, spine_w - 8)))
        spine_text = f"{title}  ·  {author}"
        # Vertical text via rotated strip
        tw2, th2 = _text_size(draw, spine_text, spine_font)
        strip_h = tw2 + 40
        strip_w = max(spine_w - 4, th2 + 8)
        strip = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(strip)
        sdraw.text(
            ((strip_w - th2) // 2, 20),
            spine_text,
            font=spine_font,
            fill=(255, 255, 255, 255),
        )
        # Rotate so text reads bottom→top when book is upright on shelf (common trade)
        rotated = strip.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
        rx = spine_l + (spine_w - rotated.width) // 2
        ry = top + (front_h - rotated.height) // 2
        img.paste(rotated, (rx, ry), rotated if rotated.mode == "RGBA" else None)

    # --- Back ---
    back_w = back_r - back_l
    back_h = bottom - top
    bc_l, bc_t, bc_r, bc_b = _barcode_box(back_l=back_l, back_r=back_r, bottom=bottom, dpi=dpi)

    # Gentle darken so white copy stays readable on each unique palette
    overlay = Image.new("RGBA", (back_w, back_h), (12, 22, 32, 92))
    back_img = img.crop((back_l, top, back_r, bottom)).convert("RGBA")
    back_img = Image.alpha_composite(back_img, overlay)
    img.paste(back_img.convert("RGB"), (back_l, top))
    draw = ImageDraw.Draw(img)

    _back_motif(draw, (back_l, top, back_r, bottom), theme, (bc_l, bc_t, bc_r, bc_b))

    back_title_font = _font(TITLE_FONT, 52)
    body_font = _font(BODY_FONT, 34)
    small_font = _font(SUB_FONT, 28)
    back_author_font = _font(AUTHOR_FONT, 40)
    kicker_font = _font(TAG_FONT, 26)

    kicker = "A BOLD & EASY COLORING BOOK"
    kw, kh = _text_size(draw, kicker, kicker_font)
    kx = back_l + (back_w - kw) // 2
    ky = top + int(back_h * 0.07)
    _draw_text_outlined(
        draw,
        (kx, ky),
        kicker,
        font=kicker_font,
        fill=(255, 255, 255),
        stroke=tuple(theme["stroke"]),
        stroke_width=2,
    )

    chips = list(theme.get("chips") or [accent])
    chip_y = ky + kh + 22
    chip_r = 16
    gap_c = 18
    total_chips_w = len(chips) * (chip_r * 2) + (len(chips) - 1) * gap_c
    chip_x = back_l + (back_w - total_chips_w) // 2 + chip_r
    for color in chips:
        draw.ellipse(
            (chip_x - chip_r, chip_y - chip_r, chip_x + chip_r, chip_y + chip_r),
            fill=tuple(color),
            outline=(255, 255, 255),
            width=3,
        )
        chip_x += chip_r * 2 + gap_c

    label = str(theme.get("back_label", "Coloring book"))
    lw, lh = _text_size(draw, label, back_title_font)
    bx = back_l + (back_w - lw) // 2
    by = chip_y + chip_r + 28
    _draw_text_outlined(
        draw,
        (bx, by),
        label,
        font=back_title_font,
        fill=(255, 255, 255),
        stroke=tuple(theme["stroke"]),
        stroke_width=3,
    )

    aw2 = int(back_w * 0.22)
    ay = by + lh + 18
    draw.rounded_rectangle(
        (back_l + (back_w - aw2) // 2, ay, back_l + (back_w + aw2) // 2, ay + 8),
        radius=4,
        fill=accent,
    )

    blurb = one_liner
    lines = _wrap_lines(draw, blurb, body_font, int(back_w * 0.78))
    text_y = ay + 40
    for line in lines:
        lw2, lh2 = _text_size(draw, line, body_font)
        draw.text(
            (back_l + (back_w - lw2) // 2, text_y),
            line,
            font=body_font,
            fill=(245, 248, 250),
        )
        text_y += lh2 + 10

    designs = int(theme.get("designs") or max(1, page_count // 2))
    trim_label = "8.5 × 8.5 inch square" if trim == "square" else "8.5 × 11 inch paperback"
    bullets = [
        f"{designs} unique pages",
        str(theme.get("theme_bullet", "Original bold-and-easy scenes")),
        "Bold outlines, closed shapes",
        "Single-sided for markers",
        trim_label,
    ]
    text_y += 28
    for b in bullets:
        line = f"•  {b}"
        lw2, lh2 = _text_size(draw, line, small_font)
        draw.text(
            (back_l + (back_w - lw2) // 2, text_y),
            line,
            font=small_font,
            fill=(230, 240, 245),
        )
        text_y += lh2 + 14

    author_line = f"by {author}"
    aw3, ah3 = _text_size(draw, author_line, back_author_font)
    # Keep the byline left of the barcode well, above its top edge
    author_x = back_l + int(back_w * 0.08)
    author_y = min(text_y + 28, bc_t - ah3 - int(0.12 * dpi))
    draw.text((author_x, author_y), author_line, font=back_author_font, fill=(255, 255, 255))

    # Draw last so no motif or copy can land in KDP's barcode zone
    _draw_barcode_well(draw, (bc_l, bc_t, bc_r, bc_b))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(dpi, dpi), optimize=True, compress_level=9)
    dims_out = dict(dims)
    dims_out["barcode_box_px"] = [bc_l, bc_t, bc_r, bc_b]
    dims_out["barcode_note"] = (
        "Leave this well empty. KDP prints a free EAN-13 barcode here. "
        "Do not buy or paste a barcode image. Use a free KDP ISBN unless you already own one."
    )
    dims_path = out_path.parent / "dimensions.json"
    dims_path.write_text(json.dumps(dims_out, indent=2) + "\n", encoding="utf-8")
    return {"path": str(out_path), **dims_out}


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
    """CLI fallback — uses gradient + title when no themed hero is available."""
    slug = "forest-animals-30" if theme in {"forest-animals", "forest", "animals"} else "math-30"
    # Synthetic soft hero from gradient
    dims = cover_dimensions(page_count, trim=trim, paper=paper)
    tmp_hero = out_path.parent / "_tmp_hero.png"
    g = _gradient((1200, 1600), (200, 220, 210), (80, 120, 100))
    g.save(tmp_hero)
    try:
        return render_theme_cover(
            slug=slug,
            title=title,
            subtitle=subtitle,
            one_liner=subtitle,
            page_count=page_count,
            hero_path=tmp_hero,
            out_path=out_path,
            trim=trim,
            paper=paper,
        )
    finally:
        if tmp_hero.exists():
            tmp_hero.unlink()
