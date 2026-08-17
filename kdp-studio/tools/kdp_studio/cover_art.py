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

# Theme palettes — all titles share STYLE.md bold-and-easy art.
THEMES: dict[str, dict] = {
    "quiet-places-40": {
        "gradient": ((190, 220, 200), (55, 100, 75)),
        "accent": (255, 210, 130),
        "title": (255, 255, 255),
        "stroke": (30, 60, 40),
        "hero": "cover-hero-quiet.png",
        "back_label": "Breathe and color",
    },
    "stained-glass-40": {
        "gradient": ((210, 195, 240), (80, 45, 120)),
        "accent": (255, 200, 120),
        "title": (255, 255, 255),
        "stroke": (40, 20, 70),
        "hero": "cover-hero-stained-glass.png",
        "back_label": "Color the light",
    },
    "cars-40": {
        "gradient": ((180, 210, 245), (30, 70, 130)),
        "accent": (255, 180, 70),
        "title": (255, 255, 255),
        "stroke": (20, 40, 80),
        "hero": "cover-hero-cars.png",
        "back_label": "Hit the road",
    },
    "planes-40": {
        "gradient": ((190, 220, 245), (40, 90, 150)),
        "accent": (255, 200, 90),
        "title": (255, 255, 255),
        "stroke": (20, 50, 90),
        "hero": "cover-hero-planes.png",
        "back_label": "Up in the clouds",
    },
    "buildings-40": {
        "gradient": ((230, 220, 210), (90, 70, 55)),
        "accent": (255, 190, 120),
        "title": (255, 255, 255),
        "stroke": (50, 35, 25),
        "hero": "cover-hero-buildings.png",
        "back_label": "Color the skyline",
    },
    "food-40": {
        "gradient": ((255, 230, 210), (170, 80, 55)),
        "accent": (255, 210, 100),
        "title": (255, 255, 255),
        "stroke": (90, 40, 25),
        "hero": "cover-hero-food.png",
        "back_label": "Dig in and color",
    },
    "mountains-40": {
        "gradient": ((200, 225, 235), (50, 80, 105)),
        "accent": (255, 200, 120),
        "title": (255, 255, 255),
        "stroke": (25, 45, 60),
        "hero": "cover-hero-mountains.png",
        "back_label": "Reach the summit",
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


def _fit_cover(src: Image.Image, box: tuple[int, int]) -> Image.Image:
    """Cover-fit (fill) into box, center-cropped."""
    return ImageOps.fit(src.convert("RGB"), box, method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))


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
    """Render a full KDP wrap with colored hero, bold title, spine, and back."""
    theme = THEMES.get(slug, {
        "gradient": ((220, 230, 240), (60, 90, 120)),
        "accent": (255, 210, 100),
        "title": (255, 255, 255),
        "stroke": (30, 40, 60),
        "back_label": "Coloring book",
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
    fitted = _fit_cover(hero, hero_box)
    paste_x = front_l - bleed_px // 4
    paste_y = top - bleed_px
    img.paste(fitted, (paste_x, paste_y))

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
    # Soft panel atmosphere (gradient already present); add faint hero wash
    wash = ImageOps.fit(hero, (back_w, back_h), centering=(0.5, 0.5)).filter(ImageFilter.GaussianBlur(18))
    wash = ImageEnhance.Brightness(wash).enhance(0.55)
    wash = ImageEnhance.Color(wash).enhance(0.7)
    back_base = img.crop((back_l, top, back_r, bottom))
    blended = Image.blend(back_base, wash, 0.35)
    img.paste(blended, (back_l, top))
    draw = ImageDraw.Draw(img)

    # Darken for text
    overlay = Image.new("RGBA", (back_w, back_h), (15, 30, 40, 110))
    back_img = img.crop((back_l, top, back_r, bottom)).convert("RGBA")
    back_img = Image.alpha_composite(back_img, overlay)
    img.paste(back_img.convert("RGB"), (back_l, top))
    draw = ImageDraw.Draw(img)

    back_title_font = _font(TITLE_FONT, 52)
    body_font = _font(BODY_FONT, 34)
    small_font = _font(SUB_FONT, 28)
    back_author_font = _font(AUTHOR_FONT, 40)

    label = theme.get("back_label", "Coloring book")
    lw, lh = _text_size(draw, label, back_title_font)
    bx = back_l + (back_w - lw) // 2
    by = top + int(back_h * 0.10)
    _draw_text_outlined(
        draw,
        (bx, by),
        label,
        font=back_title_font,
        fill=(255, 255, 255),
        stroke=tuple(theme["stroke"]),
        stroke_width=3,
    )

    # Accent bar
    aw2 = int(back_w * 0.22)
    ay = by + lh + 22
    draw.rounded_rectangle(
        (back_l + (back_w - aw2) // 2, ay, back_l + (back_w + aw2) // 2, ay + 8),
        radius=4,
        fill=accent,
    )

    blurb = one_liner
    lines = _wrap_lines(draw, blurb, body_font, int(back_w * 0.78))
    text_y = ay + 48
    for line in lines:
        lw2, lh2 = _text_size(draw, line, body_font)
        draw.text(
            (back_l + (back_w - lw2) // 2, text_y),
            line,
            font=body_font,
            fill=(245, 248, 250),
        )
        text_y += lh2 + 10

    bullets = [
        "30 unique pages",
        "Bold outlines, closed shapes",
        "Single-sided for markers",
        "8.5 × 11 inch paperback",
    ]
    text_y += 36
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
    aw3, _ = _text_size(draw, author_line, back_author_font)
    draw.text(
        (back_l + (back_w - aw3) // 2, bottom - int(back_h * 0.14)),
        author_line,
        font=back_author_font,
        fill=(255, 255, 255),
    )

    foot = "AI-assisted artwork — disclose on KDP"
    fw2, _ = _text_size(draw, foot, small_font)
    draw.text(
        (back_l + (back_w - fw2) // 2, bottom - int(back_h * 0.07)),
        foot,
        font=small_font,
        fill=(200, 210, 220),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(dpi, dpi), optimize=True, compress_level=9)
    dims_path = out_path.parent / "dimensions.json"
    dims_path.write_text(json.dumps(dims, indent=2) + "\n", encoding="utf-8")
    return {"path": str(out_path), **dims}


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
