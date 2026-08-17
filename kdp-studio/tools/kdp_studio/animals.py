"""Original forest-animal line-art pages for coloring books (300 DPI)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from .specs import trim_box

W = 5  # default stroke


def _canvas(trim: str, dpi: int, margin_in: float):
    width_in, height_in = trim_box(trim)
    w = int(round(width_in * dpi))
    h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    return img, draw, w, h, margin


def _safe(w: int, h: int, margin: int):
    return margin, margin, w - margin, h - margin


def _line(draw, pts, width=W):
    draw.line(pts, fill=0, width=width, joint="curve")


def _ellipse(draw, box, width=W):
    draw.ellipse(box, outline=0, width=width)


def _poly(draw, pts, width=W):
    closed = list(pts) + [pts[0]]
    _line(draw, closed, width=width)


def _frame(draw, left, top, right, bottom):
    inset = 18
    draw.rectangle((left + inset, top + inset, right - inset, bottom - inset), outline=0, width=4)
    # corner leaves
    for cx, cy, ang0 in (
        (left + 70, top + 70, 0.4),
        (right - 70, top + 70, 2.2),
        (left + 70, bottom - 70, -0.5),
        (right - 70, bottom - 70, 3.5),
    ):
        for i in range(5):
            ang = ang0 + i * 0.45
            x1 = cx + math.cos(ang) * 55
            y1 = cy + math.sin(ang) * 55
            _line(draw, [(cx, cy), (x1, y1)], width=3)
            _ellipse(draw, (x1 - 14, y1 - 8, x1 + 14, y1 + 8), width=3)


def _ground(draw, left, right, y, seed):
    _line(draw, [(left + 40, y), (right - 40, y)], width=4)
    x = left + 60
    while x < right - 60:
        h = 22 + ((seed + int(x)) % 7) * 5
        _poly(draw, [(x, y), (x - 10, y - h), (x + 10, y - h)], width=3)
        x += 55 + (seed % 5) * 3


def _bush(draw, x, y, scale=1.0):
    for i, (dx, dy, r) in enumerate(((-40, -20, 45), (0, -35, 55), (40, -20, 45), (-15, -55, 35), (20, -55, 35))):
        rr = int(r * scale)
        _ellipse(draw, (x + dx * scale - rr, y + dy * scale - rr, x + dx * scale + rr, y + dy * scale + rr), width=4)


def _tree(draw, x, y, scale=1.0, seed=0):
    trunk_w = int(36 * scale)
    trunk_h = int(280 * scale)
    _poly(
        draw,
        [
            (x - trunk_w // 2, y),
            (x + trunk_w // 2, y),
            (x + trunk_w // 3, y - trunk_h),
            (x - trunk_w // 3, y - trunk_h),
        ],
        width=5,
    )
    for i, r in enumerate((170, 140, 110, 85)):
        rr = int(r * scale)
        cy = y - trunk_h - int(30 * scale) - i * int(75 * scale)
        _ellipse(draw, (x - rr, cy - rr, x + rr, cy + rr), width=5)
        if (seed + i) % 2 == 0:
            _ellipse(draw, (x - rr // 2, cy - rr // 2, x + rr // 2, cy + rr // 2), width=3)


def _mushrooms(draw, x, y, seed):
    for i in range(4):
        bx = x + i * 70
        stem_h = 45 + (seed + i) % 25
        _ellipse(draw, (bx - 12, y - stem_h, bx + 12, y), width=4)
        cap_w = 36 + (seed + i) % 16
        _ellipse(draw, (bx - cap_w, y - stem_h - 36, bx + cap_w, y - stem_h + 10), width=4)
        for j in range(4):
            px = bx - cap_w // 2 + j * max(1, cap_w // 3)
            _ellipse(draw, (px - 4, y - stem_h - 22, px + 4, y - stem_h - 14), width=2)


def _cloud(draw, x, y, scale=1.0):
    for dx, dy, r in ((-50, 0, 40), (0, -15, 50), (50, 0, 40), (20, 15, 35)):
        rr = int(r * scale)
        _ellipse(draw, (x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr), width=4)


def draw_fox(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 160 * s, cy - 50 * s, cx + 50 * s, cy + 110 * s), width=6)
    _ellipse(draw, (cx + 10 * s, cy - 110 * s, cx + 160 * s, cy + 30 * s), width=6)
    _poly(draw, [(cx + 35 * s, cy - 85 * s), (cx + 55 * s, cy - 175 * s), (cx + 85 * s, cy - 90 * s)], width=5)
    _poly(draw, [(cx + 95 * s, cy - 85 * s), (cx + 135 * s, cy - 180 * s), (cx + 145 * s, cy - 80 * s)], width=5)
    _poly(draw, [(cx + 120 * s, cy - 10 * s), (cx + 195 * s, cy + 10 * s), (cx + 125 * s, cy + 35 * s)], width=5)
    _ellipse(draw, (cx + 180 * s, cy + 2 * s, cx + 198 * s, cy + 20 * s), width=4)
    _ellipse(draw, (cx + 80 * s, cy - 55 * s, cx + 105 * s, cy - 30 * s), width=4)
    for lx in (-120, -60, -10, 30):
        _line(draw, [(cx + lx * s, cy + 90 * s), (cx + (lx - 5) * s, cy + 180 * s)], width=6)
        _ellipse(draw, (cx + (lx - 18) * s, cy + 170 * s, cx + (lx + 12) * s, cy + 195 * s), width=4)
    tail = [(cx - 150 * s - math.cos(0.2 + i * 0.2) * (100 + i * 6) * s,
             cy + 10 * s - math.sin(0.2 + i * 0.2) * (80 + i * 4) * s) for i in range(14)]
    _line(draw, tail, width=8)
    _ellipse(draw, (cx - 90 * s, cy - 10 * s, cx - 20 * s, cy + 55 * s), width=4)


def draw_deer(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 170 * s, cy - 40 * s, cx + 90 * s, cy + 100 * s), width=6)
    _ellipse(draw, (cx + 50 * s, cy - 140 * s, cx + 170 * s, cy - 10 * s), width=6)
    _line(draw, [(cx + 110 * s, cy - 30 * s), (cx + 110 * s, cy - 80 * s)], width=6)
    base = (cx + 85 * s, cy - 140 * s)
    for side in (-1, 1):
        _line(draw, [base, (base[0] + side * 70 * s, base[1] - 120 * s)], width=5)
        _line(draw, [(base[0] + side * 30 * s, base[1] - 50 * s), (base[0] + side * 90 * s, base[1] - 70 * s)], width=4)
        _line(draw, [(base[0] + side * 45 * s, base[1] - 85 * s), (base[0] + side * 15 * s, base[1] - 120 * s)], width=4)
        _line(draw, [(base[0] + side * 55 * s, base[1] - 100 * s), (base[0] + side * 95 * s, base[1] - 110 * s)], width=3)
    _ellipse(draw, (cx + 115 * s, cy - 95 * s, cx + 138 * s, cy - 72 * s), width=4)
    _ellipse(draw, (cx + 150 * s, cy - 55 * s, cx + 168 * s, cy - 37 * s), width=4)
    for lx in (-130, -70, -10, 50):
        _line(draw, [(cx + lx * s, cy + 85 * s), (cx + (lx - 15) * s, cy + 200 * s)], width=6)
        _ellipse(draw, (cx + (lx - 28) * s, cy + 190 * s, cx + (lx + 5) * s, cy + 215 * s), width=4)
    for i in range(7):
        sx = cx - 110 * s + i * 40 * s
        sy = cy + ((seed + i) % 3) * 15 * s
        _ellipse(draw, (sx, sy, sx + 22 * s, sy + 16 * s), width=3)


def draw_owl(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 140 * s, cy - 160 * s, cx + 140 * s, cy + 160 * s), width=6)
    _ellipse(draw, (cx - 105 * s, cy - 110 * s, cx + 105 * s, cy + 30 * s), width=5)
    _ellipse(draw, (cx - 70 * s, cy - 70 * s, cx - 10 * s, cy - 10 * s), width=5)
    _ellipse(draw, (cx + 10 * s, cy - 70 * s, cx + 70 * s, cy - 10 * s), width=5)
    _ellipse(draw, (cx - 50 * s, cy - 50 * s, cx - 30 * s, cy - 30 * s), width=4)
    _ellipse(draw, (cx + 30 * s, cy - 50 * s, cx + 50 * s, cy - 30 * s), width=4)
    _poly(draw, [(cx - 18 * s, cy - 5 * s), (cx + 18 * s, cy - 5 * s), (cx, cy + 35 * s)], width=5)
    _poly(draw, [(cx - 100 * s, cy - 120 * s), (cx - 120 * s, cy - 200 * s), (cx - 55 * s, cy - 145 * s)], width=5)
    _poly(draw, [(cx + 100 * s, cy - 120 * s), (cx + 120 * s, cy - 200 * s), (cx + 55 * s, cy - 145 * s)], width=5)
    for i in range(7):
        y0 = cy + 20 * s + i * 24 * s
        _line(draw, [(cx - 115 * s, y0), (cx - 25 * s, y0 + 12 * s)], width=3)
        _line(draw, [(cx + 115 * s, y0), (cx + 25 * s, y0 + 12 * s)], width=3)
    for i in range(4):
        _ellipse(draw, (cx - 35 * s, cy + 40 * s + i * 28 * s, cx + 35 * s, cy + 70 * s + i * 28 * s), width=3)
    for side in (-1, 1):
        _line(draw, [(cx + side * 30 * s, cy + 155 * s), (cx + side * 40 * s, cy + 205 * s)], width=5)
        _line(draw, [(cx + side * 40 * s, cy + 205 * s), (cx + side * 70 * s, cy + 200 * s)], width=4)
        _line(draw, [(cx + side * 40 * s, cy + 205 * s), (cx + side * 55 * s, cy + 220 * s)], width=3)


def draw_bear(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 180 * s, cy - 50 * s, cx + 150 * s, cy + 150 * s), width=6)
    _ellipse(draw, (cx + 50 * s, cy - 150 * s, cx + 210 * s, cy + 20 * s), width=6)
    _ellipse(draw, (cx + 70 * s, cy - 180 * s, cx + 120 * s, cy - 130 * s), width=5)
    _ellipse(draw, (cx + 150 * s, cy - 180 * s, cx + 200 * s, cy - 130 * s), width=5)
    _ellipse(draw, (cx + 85 * s, cy - 165 * s, cx + 110 * s, cy - 140 * s), width=3)
    _ellipse(draw, (cx + 165 * s, cy - 165 * s, cx + 190 * s, cy - 140 * s), width=3)
    _ellipse(draw, (cx + 120 * s, cy - 85 * s, cx + 155 * s, cy - 50 * s), width=4)
    _ellipse(draw, (cx + 175 * s, cy - 40 * s, cx + 205 * s, cy - 10 * s), width=4)
    for lx in (-130, -50, 30, 90):
        _line(draw, [(cx + lx * s, cy + 130 * s), (cx + lx * s, cy + 210 * s)], width=7)
        _ellipse(draw, (cx + (lx - 25) * s, cy + 200 * s, cx + (lx + 25) * s, cy + 230 * s), width=4)
    _ellipse(draw, (cx - 80 * s, cy - 5 * s, cx + 70 * s, cy + 115 * s), width=4)


def draw_rabbit(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 100 * s, cy - 30 * s, cx + 100 * s, cy + 140 * s), width=6)
    _ellipse(draw, (cx - 70 * s, cy - 120 * s, cx + 70 * s, cy), width=6)
    _ellipse(draw, (cx - 65 * s, cy - 280 * s, cx - 20 * s, cy - 100 * s), width=5)
    _ellipse(draw, (cx + 20 * s, cy - 290 * s, cx + 65 * s, cy - 100 * s), width=5)
    _ellipse(draw, (cx - 52 * s, cy - 240 * s, cx - 32 * s, cy - 120 * s), width=3)
    _ellipse(draw, (cx + 32 * s, cy - 250 * s, cx + 52 * s, cy - 120 * s), width=3)
    _ellipse(draw, (cx - 40 * s, cy - 75 * s, cx - 15 * s, cy - 50 * s), width=4)
    _ellipse(draw, (cx + 15 * s, cy - 75 * s, cx + 40 * s, cy - 50 * s), width=4)
    _ellipse(draw, (cx - 16 * s, cy - 40 * s, cx + 16 * s, cy - 12 * s), width=4)
    _ellipse(draw, (cx - 115 * s, cy + 110 * s, cx - 35 * s, cy + 165 * s), width=5)
    _ellipse(draw, (cx + 35 * s, cy + 110 * s, cx + 115 * s, cy + 165 * s), width=5)
    _ellipse(draw, (cx - 140 * s, cy + 50 * s, cx - 85 * s, cy + 105 * s), width=5)
    # whiskers
    for dy in (-8, 8, 20):
        _line(draw, [(cx - 10 * s, cy - 20 * s + dy * s), (cx - 70 * s, cy - 30 * s + dy * s)], width=2)
        _line(draw, [(cx + 10 * s, cy - 20 * s + dy * s), (cx + 70 * s, cy - 30 * s + dy * s)], width=2)


def draw_squirrel(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 80 * s, cy - 20 * s, cx + 70 * s, cy + 130 * s), width=6)
    _ellipse(draw, (cx + 10 * s, cy - 100 * s, cx + 130 * s, cy + 20 * s), width=6)
    _ellipse(draw, (cx + 70 * s, cy - 70 * s, cx + 95 * s, cy - 45 * s), width=4)
    _poly(draw, [(cx + 40 * s, cy - 85 * s), (cx + 55 * s, cy - 145 * s), (cx + 75 * s, cy - 85 * s)], width=4)
    _poly(draw, [(cx + 105 * s, cy - 25 * s), (cx + 150 * s, cy - 10 * s), (cx + 108 * s, cy + 5 * s)], width=4)
    pts = [(cx - 50 * s - math.cos(-0.3 + i * 0.2) * (110 + i * 5) * s,
            cy + 30 * s - math.sin(-0.3 + i * 0.2) * (130 + i * 4) * s) for i in range(18)]
    _line(draw, pts, width=9)
    _ellipse(draw, (cx + 85 * s, cy + 50 * s, cx + 140 * s, cy + 110 * s), width=4)
    _line(draw, [(cx + 90 * s, cy + 70 * s), (cx + 135 * s, cy + 70 * s)], width=4)
    _line(draw, [(cx + 112 * s, cy + 50 * s), (cx + 112 * s, cy + 28 * s)], width=3)
    for lx in (-40, 20):
        _line(draw, [(cx + lx * s, cy + 120 * s), (cx + lx * s, cy + 175 * s)], width=5)


def draw_raccoon(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 150 * s, cy - 30 * s, cx + 110 * s, cy + 120 * s), width=6)
    _ellipse(draw, (cx + 40 * s, cy - 120 * s, cx + 180 * s, cy + 20 * s), width=6)
    _ellipse(draw, (cx + 55 * s, cy - 85 * s, cx + 115 * s, cy - 30 * s), width=4)
    _ellipse(draw, (cx + 120 * s, cy - 85 * s, cx + 180 * s, cy - 30 * s), width=4)
    _ellipse(draw, (cx + 75 * s, cy - 70 * s, cx + 98 * s, cy - 47 * s), width=4)
    _ellipse(draw, (cx + 140 * s, cy - 70 * s, cx + 163 * s, cy - 47 * s), width=4)
    _ellipse(draw, (cx + 115 * s, cy - 30 * s, cx + 145 * s, cy - 5 * s), width=4)
    _poly(draw, [(cx + 60 * s, cy - 110 * s), (cx + 80 * s, cy - 165 * s), (cx + 105 * s, cy - 110 * s)], width=4)
    _poly(draw, [(cx + 130 * s, cy - 110 * s), (cx + 155 * s, cy - 165 * s), (cx + 175 * s, cy - 108 * s)], width=4)
    for i in range(7):
        x0 = cx - 160 * s - i * 32 * s
        y0 = cy + 40 * s + math.sin(i * 0.8) * 18 * s
        _ellipse(draw, (x0, y0, x0 + 50 * s, y0 + 34 * s), width=4)
    for lx in (-100, -35, 25, 70):
        _line(draw, [(cx + lx * s, cy + 100 * s), (cx + lx * s, cy + 190 * s)], width=6)


def draw_hedgehog(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 170 * s, cy - 50 * s, cx + 130 * s, cy + 110 * s), width=6)
    _ellipse(draw, (cx + 70 * s, cy - 15 * s, cx + 175 * s, cy + 90 * s), width=5)
    _ellipse(draw, (cx + 115 * s, cy + 15 * s, cx + 140 * s, cy + 40 * s), width=4)
    _ellipse(draw, (cx + 155 * s, cy + 40 * s, cx + 172 * s, cy + 57 * s), width=4)
    for i in range(24):
        ang = math.pi * 0.05 + i * (math.pi * 0.95 / 23)
        x0 = cx - 10 * s + math.cos(ang) * 70 * s
        y0 = cy + 10 * s + math.sin(ang) * 25 * s
        reach = 150 + (seed + i) % 35
        x1 = cx - 10 * s + math.cos(ang) * reach * s
        y1 = cy + 10 * s + math.sin(ang) * (reach * 0.7) * s - 50 * s
        _line(draw, [(x0, y0), (x1, y1)], width=4)
    _ellipse(draw, (cx - 60 * s, cy + 90 * s, cx + 5 * s, cy + 130 * s), width=4)
    _ellipse(draw, (cx + 50 * s, cy + 95 * s, cx + 110 * s, cy + 135 * s), width=4)


def draw_bird(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 120 * s, cy - 50 * s, cx + 90 * s, cy + 90 * s), width=6)
    _ellipse(draw, (cx + 50 * s, cy - 100 * s, cx + 150 * s, cy), width=6)
    _poly(draw, [(cx + 135 * s, cy - 50 * s), (cx + 200 * s, cy - 35 * s), (cx + 138 * s, cy - 18 * s)], width=4)
    _ellipse(draw, (cx + 90 * s, cy - 70 * s, cx + 115 * s, cy - 45 * s), width=4)
    _ellipse(draw, (cx - 90 * s, cy - 25 * s, cx + 40 * s, cy + 55 * s), width=5)
    for i in range(5):
        y = cy - 10 * s + i * 14 * s
        _line(draw, [(cx - 70 * s, y), (cx + 20 * s, y + 8 * s)], width=3)
    for i in range(5):
        _line(draw, [(cx - 100 * s, cy + 25 * s), (cx - 190 * s, cy - 20 * s + i * 22 * s)], width=4)
    _line(draw, [(cx - 220 * s, cy + 100 * s), (cx + 220 * s, cy + 100 * s)], width=5)
    # leaves on branch
    for i in range(6):
        lx = cx - 180 * s + i * 70 * s
        _ellipse(draw, (lx, cy + 70 * s, lx + 45 * s, cy + 100 * s), width=3)
        _line(draw, [(lx + 22 * s, cy + 100 * s), (lx + 22 * s, cy + 100 * s)], width=2)
    _line(draw, [(cx - 15 * s, cy + 85 * s), (cx - 15 * s, cy + 100 * s)], width=4)
    _line(draw, [(cx + 25 * s, cy + 85 * s), (cx + 25 * s, cy + 100 * s)], width=4)


def draw_wolf(draw, cx, cy, scale=1.0, seed=0):
    s = scale
    _ellipse(draw, (cx - 170 * s, cy - 30 * s, cx + 80 * s, cy + 110 * s), width=6)
    _ellipse(draw, (cx + 30 * s, cy - 130 * s, cx + 180 * s, cy + 20 * s), width=6)
    _poly(draw, [(cx + 50 * s, cy - 110 * s), (cx + 70 * s, cy - 185 * s), (cx + 100 * s, cy - 115 * s)], width=5)
    _poly(draw, [(cx + 115 * s, cy - 110 * s), (cx + 150 * s, cy - 190 * s), (cx + 170 * s, cy - 108 * s)], width=5)
    _poly(draw, [(cx + 125 * s, cy - 25 * s), (cx + 205 * s, cy - 5 * s), (cx + 130 * s, cy + 20 * s)], width=5)
    _ellipse(draw, (cx + 85 * s, cy - 70 * s, cx + 110 * s, cy - 45 * s), width=4)
    for lx in (-130, -65, -5, 45):
        _line(draw, [(cx + lx * s, cy + 95 * s), (cx + lx * s, cy + 195 * s)], width=6)
        _ellipse(draw, (cx + (lx - 20) * s, cy + 185 * s, cx + (lx + 18) * s, cy + 210 * s), width=4)
    for i in range(5):
        _line(draw, [(cx - 60 * s, cy + i * 18 * s), (cx + 30 * s, cy + 15 * s + i * 18 * s)], width=3)
    # moon for howl vibe
    _ellipse(draw, (cx + 160 * s, cy - 220 * s, cx + 240 * s, cy - 140 * s), width=4)


ANIMALS = [
    ("fox", draw_fox),
    ("deer", draw_deer),
    ("owl", draw_owl),
    ("bear", draw_bear),
    ("rabbit", draw_rabbit),
    ("squirrel", draw_squirrel),
    ("raccoon", draw_raccoon),
    ("hedgehog", draw_hedgehog),
    ("bird", draw_bird),
    ("wolf", draw_wolf),
]


def page_forest_animal(seed: int, trim: str = "letter", dpi: int = 300, margin_in: float = 0.5) -> Image.Image:
    img, draw, w, h, margin = _canvas(trim, dpi, margin_in)
    left, top, right, bottom = _safe(w, h, margin)
    _frame(draw, left, top, right, bottom)

    name, drawer = ANIMALS[(seed - 1) % len(ANIMALS)]
    ground_y = bottom - int(0.12 * (bottom - top))
    _ground(draw, left + 30, right - 30, ground_y, seed)

    variant = seed % 5
    if variant == 0:
        _tree(draw, left + 200, ground_y, scale=1.05, seed=seed)
        _bush(draw, right - 220, ground_y, scale=1.1)
        _cloud(draw, right - 280, top + 180, scale=1.0)
    elif variant == 1:
        _tree(draw, right - 210, ground_y, scale=0.95, seed=seed)
        _mushrooms(draw, left + 100, ground_y, seed)
        _cloud(draw, left + 280, top + 160, scale=0.9)
    elif variant == 2:
        _tree(draw, left + 180, ground_y, scale=0.75, seed=seed)
        _tree(draw, right - 190, ground_y, scale=0.65, seed=seed + 2)
        _bush(draw, (left + right) // 2 - 200, ground_y, scale=0.9)
    elif variant == 3:
        _mushrooms(draw, right - 280, ground_y, seed)
        _bush(draw, left + 180, ground_y, scale=1.2)
        _cloud(draw, (left + right) // 2, top + 150, scale=1.1)
    else:
        _tree(draw, left + 160, ground_y, scale=0.7, seed=seed)
        _mushrooms(draw, left + 320, ground_y, seed)
        _bush(draw, right - 200, ground_y, scale=1.0)

    cx = (left + right) // 2 + ((seed % 5) - 2) * 30
    cy = (top + bottom) // 2 + 40
    scale = 1.55 if trim == "letter" else 1.25
    drawer(draw, cx, cy, scale=scale, seed=seed)
    return img


def generate_forest_pages(
    out_dir: Path,
    count: int = 30,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i in range(count):
        img = page_forest_animal(seed=i + 1, trim=trim, dpi=dpi, margin_in=margin_in)
        path = out_dir / f"page-{i + 1:02d}.png"
        img.save(path, dpi=(dpi, dpi))
        paths.append(path)
    return paths
