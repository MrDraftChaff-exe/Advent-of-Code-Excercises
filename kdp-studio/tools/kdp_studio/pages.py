"""Generate original black-line geometric coloring pages (300 DPI)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from .specs import trim_box


def _canvas(trim: str, dpi: int, margin_in: float) -> tuple[Image.Image, ImageDraw.ImageDraw, int, int, int]:
    width_in, height_in = trim_box(trim)
    w = int(round(width_in * dpi))
    h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    return img, draw, w, h, margin


def _safe_box(w: int, h: int, margin: int) -> tuple[int, int, int, int]:
    return margin, margin, w - margin, h - margin


def page_mandala(seed: int, trim: str = "letter", dpi: int = 300, margin_in: float = 0.5) -> Image.Image:
    img, draw, w, h, margin = _canvas(trim, dpi, margin_in)
    cx, cy = w // 2, h // 2
    left, top, right, bottom = _safe_box(w, h, margin)
    max_r = min(cx - left, cy - top, right - cx, bottom - cy) - 8
    rings = 6 + (seed % 5)
    petals = 8 + (seed % 10)
    for i in range(1, rings + 1):
        r = int(max_r * i / rings)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=0, width=3)
    for i in range(petals):
        angle = (2 * math.pi * i / petals) + (seed * 0.17)
        x = cx + int(math.cos(angle) * max_r * 0.92)
        y = cy + int(math.sin(angle) * max_r * 0.92)
        draw.line((cx, cy, x, y), fill=0, width=3)
        pr = int(max_r * (0.12 + (seed % 4) * 0.02))
        ox = cx + int(math.cos(angle) * max_r * 0.55)
        oy = cy + int(math.sin(angle) * max_r * 0.55)
        draw.ellipse((ox - pr, oy - pr, ox + pr, oy + pr), outline=0, width=2)
    inner = int(max_r * 0.18)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), outline=0, width=4)
    return img


def page_lattice(seed: int, trim: str = "letter", dpi: int = 300, margin_in: float = 0.5) -> Image.Image:
    img, draw, w, h, margin = _canvas(trim, dpi, margin_in)
    left, top, right, bottom = _safe_box(w, h, margin)
    cols = 6 + (seed % 5)
    rows = 8 + (seed % 5)
    dx = (right - left) / cols
    dy = (bottom - top) / rows
    for r in range(rows + 1):
        y = top + int(r * dy)
        draw.line((left, y, right, y), fill=0, width=2)
    for c in range(cols + 1):
        x = left + int(c * dx)
        draw.line((x, top, x, bottom), fill=0, width=2)
    for r in range(rows):
        for c in range(cols):
            if (r + c + seed) % 3 == 0:
                x0 = left + int(c * dx)
                y0 = top + int(r * dy)
                x1 = left + int((c + 1) * dx)
                y1 = top + int((r + 1) * dy)
                draw.line((x0, y0, x1, y1), fill=0, width=2)
                draw.line((x0, y1, x1, y0), fill=0, width=2)
            elif (r + c + seed) % 3 == 1:
                x0 = left + int(c * dx) + 6
                y0 = top + int(r * dy) + 6
                x1 = left + int((c + 1) * dx) - 6
                y1 = top + int((r + 1) * dy) - 6
                draw.ellipse((x0, y0, x1, y1), outline=0, width=2)
    return img


def page_hex_bloom(seed: int, trim: str = "letter", dpi: int = 300, margin_in: float = 0.5) -> Image.Image:
    img, draw, w, h, margin = _canvas(trim, dpi, margin_in)
    left, top, right, bottom = _safe_box(w, h, margin)
    size = 70 + (seed % 5) * 8
    dx = size * 1.5
    dy = size * math.sqrt(3)
    y = top + size
    row = 0
    while y < bottom - size:
        x_off = (size * 0.75) if row % 2 else 0
        x = left + size + x_off
        while x < right - size:
            pts = []
            for i in range(6):
                a = math.pi / 6 + i * math.pi / 3 + (seed % 2) * (math.pi / 12)
                pts.append((x + size * math.cos(a), y + size * math.sin(a)))
            draw.polygon(pts, outline=0, width=2)
            for i in range(6):
                draw.line((x, y, pts[i][0], pts[i][1]), fill=0, width=1)
            x += dx
        y += dy / 2
        row += 1
    return img


def page_waves(seed: int, trim: str = "letter", dpi: int = 300, margin_in: float = 0.5) -> Image.Image:
    img, draw, w, h, margin = _canvas(trim, dpi, margin_in)
    left, top, right, bottom = _safe_box(w, h, margin)
    amp = 18 + (seed % 7) * 4
    wavelength = 90 + (seed % 6) * 20
    gap = 28 + (seed % 4) * 4
    y = top + 20
    phase = seed * 0.4
    while y < bottom - 20:
        pts = []
        x = left
        while x <= right:
            yy = y + amp * math.sin((x / wavelength) * 2 * math.pi + phase)
            pts.append((x, yy))
            x += 4
        draw.line(pts, fill=0, width=2)
        y += gap
        phase += 0.35
    # vertical guides for “stained glass” feel
    step = 110 + (seed % 5) * 15
    x = left + step // 2
    while x < right:
        draw.line((x, top, x, bottom), fill=0, width=2)
        x += step
    return img


GENERATORS = [page_mandala, page_lattice, page_hex_bloom, page_waves]


def generate_pages(
    out_dir: Path,
    count: int = 30,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i in range(count):
        gen = GENERATORS[i % len(GENERATORS)]
        img = gen(seed=i + 1, trim=trim, dpi=dpi, margin_in=margin_in)
        path = out_dir / f"page-{i + 1:02d}.png"
        img.save(path, dpi=(dpi, dpi))
        paths.append(path)
    return paths
