#!/usr/bin/env python3
"""DEPRECATED — do not use for Quiet Places production art.

Procedural geometry here produced sparse clip-art (triangle mountains, hex junk)
that does not match bold-and-easy hand-drawn stress-relief books.

Production path:
  1. Generate illustrated scenes (qp-gen-*.png)
  2. python3 scripts/inkify_quiet_places.py [src_dir]
  3. python3 scripts/build_theme_book.py quiet-places-40
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 2048
MARGIN = 80
STROKE = 16
STROKE_MED = 10
STROKE_THIN = 7
INK = (20, 20, 20)
WHITE = (255, 255, 255)


def _new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (SIZE, SIZE), WHITE)
    return im, ImageDraw.Draw(im)


def _poly(d: ImageDraw.ImageDraw, pts: list[tuple[float, float]], width: int = STROKE) -> None:
    ip = [(int(x), int(y)) for x, y in pts]
    d.line(ip + [ip[0]], fill=INK, width=width, joint="curve")


def _line(d: ImageDraw.ImageDraw, pts: list[tuple[float, float]], width: int = STROKE) -> None:
    ip = [(int(x), int(y)) for x, y in pts]
    d.line(ip, fill=INK, width=width, joint="curve")


def _ellipse(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float], width: int = STROKE) -> None:
    d.ellipse([int(v) for v in box], outline=INK, width=width)


def _circle(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, width: int = STROKE) -> None:
    _ellipse(d, (cx - r, cy - r, cx + r, cy + r), width)


def _arc_pts(cx: float, cy: float, r: float, a0: float, a1: float, n: int = 40) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        rad = math.radians(t)
        pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
    return pts


def _hill(d: ImageDraw.ImageDraw, y: float, amp: float, phase: float, steps: int = 48) -> None:
    pts = []
    for i in range(steps + 1):
        x = MARGIN + (SIZE - 2 * MARGIN) * i / steps
        yy = y + amp * math.sin(i / steps * math.pi * 2 + phase)
        pts.append((x, yy))
    _line(d, pts, STROKE)


def _tree(d: ImageDraw.ImageDraw, x: float, y: float, h: float) -> None:
    # trunk
    tw = h * 0.12
    _poly(d, [(x - tw, y), (x + tw, y), (x + tw * 0.7, y - h * 0.35), (x - tw * 0.7, y - h * 0.35)])
    # foliage tiers
    for i, frac in enumerate((0.55, 0.4, 0.28)):
        top = y - h * (0.35 + 0.22 * (i + 1))
        mid = y - h * (0.28 + 0.2 * i)
        w = h * frac
        _poly(d, [(x, top), (x + w, mid), (x - w, mid)])


def _sun(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    _circle(d, cx, cy, r)
    for i in range(8):
        a = i * 45
        rad = math.radians(a)
        x0 = cx + (r + 18) * math.cos(rad)
        y0 = cy + (r + 18) * math.sin(rad)
        x1 = cx + (r + 55) * math.cos(rad)
        y1 = cy + (r + 55) * math.sin(rad)
        _line(d, [(x0, y0), (x1, y1)], STROKE_MED)


def _cloud(d: ImageDraw.ImageDraw, x: float, y: float, s: float) -> None:
    _circle(d, x, y, s * 0.45, STROKE_MED)
    _circle(d, x + s * 0.45, y - s * 0.1, s * 0.38, STROKE_MED)
    _circle(d, x + s * 0.9, y, s * 0.42, STROKE_MED)
    _circle(d, x + s * 0.4, y + s * 0.15, s * 0.35, STROKE_MED)


def _flower(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, petals: int = 6) -> None:
    for i in range(petals):
        a = i * (360 / petals)
        rad = math.radians(a)
        px = cx + r * 0.55 * math.cos(rad)
        py = cy + r * 0.55 * math.sin(rad)
        _ellipse(d, (px - r * 0.45, py - r * 0.28, px + r * 0.45, py + r * 0.28), STROKE_MED)
    _circle(d, cx, cy, r * 0.28, STROKE)


def _mushroom(d: ImageDraw.ImageDraw, x: float, y: float, h: float) -> None:
    stem_w = h * 0.22
    # stem
    _poly(
        d,
        [
            (x - stem_w, y),
            (x + stem_w, y),
            (x + stem_w * 0.85, y - h * 0.55),
            (x - stem_w * 0.85, y - h * 0.55),
        ],
    )
    # cap
    cap_w = h * 0.7
    cap_h = h * 0.4
    cy = y - h * 0.55
    _ellipse(d, (x - cap_w, cy - cap_h, x + cap_w, cy + cap_h * 0.35), STROKE)
    # spots
    for ox, oy, rr in ((-0.25, -0.15, 0.12), (0.15, -0.2, 0.1), (0.0, 0.0, 0.08)):
        _circle(d, x + cap_w * ox, cy + cap_h * oy, cap_w * rr, STROKE_THIN)


def _cabin(d: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float) -> None:
    # walls
    _poly(d, [(x, y), (x + w, y), (x + w, y - h * 0.55), (x, y - h * 0.55)])
    # roof
    _poly(d, [(x - w * 0.08, y - h * 0.55), (x + w / 2, y - h), (x + w + w * 0.08, y - h * 0.55)])
    # door
    dw, dh = w * 0.22, h * 0.32
    _poly(d, [(x + w * 0.4, y), (x + w * 0.4 + dw, y), (x + w * 0.4 + dw, y - dh), (x + w * 0.4, y - dh)])
    # window
    ww = w * 0.18
    wx, wy = x + w * 0.15, y - h * 0.35
    _poly(d, [(wx, wy), (wx + ww, wy), (wx + ww, wy - ww), (wx, wy - ww)])
    _line(d, [(wx + ww / 2, wy), (wx + ww / 2, wy - ww)], STROKE_THIN)
    _line(d, [(wx, wy - ww / 2), (wx + ww, wy - ww / 2)], STROKE_THIN)


def _bird(d: ImageDraw.ImageDraw, x: float, y: float, s: float) -> None:
    _ellipse(d, (x - s, y - s * 0.7, x + s * 0.6, y + s * 0.7), STROKE)
    _circle(d, x + s * 0.55, y - s * 0.15, s * 0.45, STROKE)
    _circle(d, x + s * 0.7, y - s * 0.25, s * 0.1, STROKE_THIN)  # eye
    _poly(d, [(x + s * 0.95, y - s * 0.1), (x + s * 1.35, y), (x + s * 0.95, y + s * 0.15)])  # beak
    _poly(d, [(x - s * 0.1, y), (x - s * 0.9, y - s * 0.5), (x - s * 0.3, y + s * 0.2)])  # wing


def _frame(d: ImageDraw.ImageDraw) -> None:
    """No page frame — keeps designs open and lets import enrichment fill sparse bands."""
    return


# ---- Scene builders ----

def scene_mountain_lake(seed: int) -> Image.Image:
    rng = random.Random(seed)
    im, d = _new()
    _sun(d, 1550, 320, 110)
    _cloud(d, 280, 280, 180)
    _cloud(d, 700, 240, 120)
    # mountains
    _poly(d, [(MARGIN, 1050), (450, 420), (780, 920), (1050, 480), (1350, 900), (1650, 400), (SIZE - MARGIN, 1050)])
    # ridge details
    _line(d, [(450, 420), (500, 700), (600, 550)], STROKE_THIN)
    _line(d, [(1650, 400), (1600, 680), (1500, 520)], STROKE_THIN)
    # lake
    _ellipse(d, (220, 1000, 1820, 1600), STROKE)
    _line(d, [(400, 1200), (700, 1230), (1000, 1180), (1350, 1240), (1650, 1190)], STROKE_THIN)
    _line(d, [(500, 1350), (900, 1380), (1400, 1340)], STROKE_THIN)
    # shore trees + flowers
    for x in (280, 420, 560, 1500, 1640, 1780):
        _tree(d, x, 1040, rng.uniform(200, 300))
    for x, y, rr in ((700, 1650, 55), (900, 1700, 45), (1100, 1660, 50), (1300, 1710, 40)):
        _flower(d, x, y, rr)
    _mushroom(d, 650, 1020, 90)
    _frame(d)
    return im


def scene_rolling_hills(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 400, 360, 100)
    _hill(d, 900, 80, 0.2)
    _hill(d, 1100, 100, 1.1)
    _hill(d, 1350, 70, 2.0)
    for x in (300, 550, 900, 1300, 1600):
        _tree(d, x, 1350 + (x % 70), 220 + (x % 90))
    _flower(d, 700, 1550, 70)
    _flower(d, 1100, 1600, 60)
    _flower(d, 1450, 1520, 55)
    _frame(d)
    return im


def scene_cabin_woods(seed: int) -> Image.Image:
    im, d = _new()
    _cloud(d, 1200, 300, 180)
    _cabin(d, 700, 1300, 620, 520)
    for x, h in ((280, 340), (420, 280), (1450, 360), (1650, 300), (1780, 250)):
        _tree(d, x, 1350, h)
    _hill(d, 1450, 40, 0.5)
    _mushroom(d, 560, 1380, 120)
    _mushroom(d, 1380, 1400, 100)
    _frame(d)
    return im


def scene_beach(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 1600, 400, 110)
    # waves
    for i, y in enumerate((900, 1050, 1200, 1350)):
        pts = []
        for j in range(40):
            x = MARGIN + (SIZE - 2 * MARGIN) * j / 39
            yy = y + 35 * math.sin(j / 39 * math.pi * 3 + i)
            pts.append((x, yy))
        _line(d, pts, STROKE)
    # island
    _ellipse(d, (700, 700, 1300, 900), STROKE)
    _tree(d, 950, 820, 200)  # palm-ish as triangle tree
    _poly(d, [(1000, 820), (1180, 700), (1080, 820)], STROKE)  # second frond
    # shell
    _ellipse(d, (400, 1500, 580, 1620), STROKE)
    _line(d, [(490, 1510), (490, 1610)], STROKE_THIN)
    _frame(d)
    return im


def scene_waterfall(seed: int) -> Image.Image:
    im, d = _new()
    _poly(d, [(MARGIN, 700), (600, 400), (900, 650), (MARGIN, 900)])  # left cliff
    _poly(d, [(SIZE - MARGIN, 650), (1400, 380), (1150, 620), (SIZE - MARGIN, 850)])
    # falls
    for x in (920, 1000, 1080):
        _line(d, [(x, 620), (x - 20, 1400)], STROKE)
    _ellipse(d, (650, 1350, 1350, 1650), STROKE)  # pool
    _tree(d, 350, 950, 260)
    _tree(d, 1650, 900, 240)
    _frame(d)
    return im


def scene_desert(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 1500, 350, 120)
    _hill(d, 1200, 90, 0.8)
    _hill(d, 1450, 60, 2.2)
    # cacti
    for x, h in ((450, 420), (900, 520), (1400, 380)):
        _poly(d, [(x - 40, 1450), (x + 40, 1450), (x + 35, 1450 - h), (x - 35, 1450 - h)])
        # arms
        _poly(d, [(x + 35, 1450 - h * 0.55), (x + 140, 1450 - h * 0.55), (x + 140, 1450 - h * 0.75), (x + 35, 1450 - h * 0.7)])
        _poly(d, [(x - 35, 1450 - h * 0.4), (x - 130, 1450 - h * 0.4), (x - 130, 1450 - h * 0.6), (x - 35, 1450 - h * 0.55)])
    _frame(d)
    return im


def scene_lighthouse(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 400, 380, 80)
    # cliff
    _poly(d, [(MARGIN, 1600), (200, 1000), (700, 1100), (900, 1600)])
    # tower
    _poly(d, [(1050, 1500), (1250, 1500), (1220, 550), (1080, 550)])
    _poly(d, [(1040, 550), (1260, 550), (1260, 480), (1040, 480)])  # lantern room
    _poly(d, [(1060, 480), (1150, 380), (1240, 480)])  # roof
    # stripes
    for y in (700, 900, 1100, 1300):
        _line(d, [(1085, y), (1225, y)], STROKE_MED)
    # waves
    for y in (1550, 1650, 1750):
        pts = [(x, y + 20 * math.sin(x / 80)) for x in range(900, 1900, 40)]
        _line(d, pts, STROKE_MED)
    _frame(d)
    return im


def scene_snowy_cabin(seed: int) -> Image.Image:
    im, d = _new()
    for cx, cy in ((400, 350), (700, 280), (1100, 320), (1500, 260), (1700, 380)):
        _circle(d, cx, cy, 18, STROKE_THIN)  # snowflakes-ish dots as small stars
        _line(d, [(cx - 30, cy), (cx + 30, cy)], STROKE_THIN)
        _line(d, [(cx, cy - 30), (cx, cy + 30)], STROKE_THIN)
    _cabin(d, 650, 1350, 700, 560)
    _hill(d, 1450, 50, 1.5)
    for x in (280, 450, 1550, 1720):
        _tree(d, x, 1400, 300)
    _frame(d)
    return im


def scene_meadow_path(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 1600, 360, 95)
    _hill(d, 850, 70, 0.4)
    # path
    _poly(d, [(850, 900), (1100, 900), (1400, 1750), (550, 1750)])
    # flowers along path
    for x, y, r in (
        (400, 1100, 70),
        (550, 1300, 55),
        (350, 1500, 65),
        (1500, 1150, 60),
        (1650, 1350, 70),
        (1550, 1550, 50),
        (700, 1000, 45),
        (1200, 1050, 50),
    ):
        _flower(d, x, y, r)
    _tree(d, 300, 880, 240)
    _tree(d, 1750, 900, 260)
    _frame(d)
    return im


def scene_hot_air_balloon(seed: int) -> Image.Image:
    im, d = _new()
    _hill(d, 1500, 60, 0.9)
    # balloon
    _ellipse(d, (700, 350, 1300, 1050), STROKE)
    for a in (-40, -15, 15, 40):
        pts = _arc_pts(1000, 700, 280, 200 + a, 340 + a, 20)
        _line(d, pts, STROKE_THIN)
    # basket
    _poly(d, [(920, 1200), (1080, 1200), (1100, 1350), (900, 1350)])
    _line(d, [(820, 950), (920, 1200)], STROKE_MED)
    _line(d, [(1180, 950), (1080, 1200)], STROKE_MED)
    _cloud(d, 350, 500, 140)
    _cloud(d, 1500, 450, 120)
    _frame(d)
    return im


def scene_island(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 400, 400, 90)
    _ellipse(d, (450, 900, 1600, 1400), STROKE)
    _tree(d, 900, 1050, 280)
    _tree(d, 1150, 1080, 220)
    _circle(d, 1300, 1120, 40, STROKE)  # rock
    for y in (1500, 1600, 1700):
        pts = [(x, y + 25 * math.sin(x / 90 + y)) for x in range(MARGIN, SIZE - MARGIN, 35)]
        _line(d, pts, STROKE_MED)
    _bird(d, 1500, 500, 70)
    _frame(d)
    return im


def scene_canyon(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 1000, 320, 85)
    # layered canyon walls
    layers = [
        [(200, 700), (600, 550), (1000, 680), (1400, 520), (1850, 700), (1850, 1750), (200, 1750)],
        [(350, 950), (700, 820), (1100, 980), (1500, 800), (1700, 950), (1700, 1750), (350, 1750)],
    ]
    for layer in layers:
        _poly(d, layer, STROKE)
    # river
    _poly(d, [(900, 1200), (1050, 1200), (1150, 1750), (800, 1750)], STROKE)
    _frame(d)
    return im


# Flowers / botanical

def scene_sunflower(seed: int) -> Image.Image:
    im, d = _new()
    cx, cy, r = 1024, 780, 360
    for i in range(16):
        a = i * 22.5
        rad = math.radians(a)
        px = cx + r * 0.85 * math.cos(rad)
        py = cy + r * 0.85 * math.sin(rad)
        _ellipse(d, (px - 90, py - 40, px + 90, py + 40), STROKE)
    _circle(d, cx, cy, 160, STROKE)
    # seed dots
    for i in range(12):
        a = i * 30
        rad = math.radians(a)
        _circle(d, cx + 70 * math.cos(rad), cy + 70 * math.sin(rad), 12, STROKE_THIN)
    # stem + leaves
    _line(d, [(cx, cy + 160), (cx, 1750)], STROKE)
    _poly(d, [(cx, 1300), (cx - 180, 1200), (cx - 40, 1350)])
    _poly(d, [(cx, 1450), (cx + 180, 1350), (cx + 40, 1500)])
    for x, y, rr in ((350, 1600, 70), (550, 1700, 55), (1500, 1620, 65), (1700, 1720, 50)):
        _flower(d, x, y, rr)
    _hill(d, 1750, 25, 0.4)
    _frame(d)
    return im


def scene_tulip_row(seed: int) -> Image.Image:
    im, d = _new()
    for i, x in enumerate((400, 700, 1000, 1300, 1600)):
        y = 1400
        _line(d, [(x, y), (x, y - 420)], STROKE)
        # tulip head
        _poly(d, [(x - 80, y - 420), (x, y - 560), (x + 80, y - 420), (x + 50, y - 380), (x - 50, y - 380)])
        _line(d, [(x - 40, y - 480), (x, y - 420), (x + 40, y - 480)], STROKE_THIN)
        # leaf
        side = -1 if i % 2 == 0 else 1
        _poly(d, [(x, y - 200), (x + side * 160, y - 280), (x + side * 20, y - 150)])
    _hill(d, 1550, 30, 0.3)
    _frame(d)
    return im


def scene_daisy_field(seed: int) -> Image.Image:
    im, d = _new()
    coords = [
        (400, 500), (900, 420), (1400, 520), (600, 850), (1100, 780), (1550, 900),
        (350, 1200), (800, 1150), (1250, 1250), (1650, 1180), (500, 1550), (1000, 1500), (1450, 1580),
    ]
    for i, (x, y) in enumerate(coords):
        _flower(d, x, y, 70 + (i % 4) * 12, petals=8)
    _frame(d)
    return im


def scene_lotus(seed: int) -> Image.Image:
    im, d = _new()
    cx, cy = 1024, 1100
    for scale in (1.0, 0.75, 0.5):
        for i in range(6):
            a = i * 60 + (0 if scale == 1 else 30)
            rad = math.radians(a)
            px = cx + 220 * scale * math.cos(rad)
            py = cy - 40 + 120 * scale * math.sin(rad)
            _ellipse(d, (px - 100 * scale, py - 160 * scale, px + 100 * scale, py + 40 * scale), STROKE)
    _ellipse(d, (cx - 70, cy - 50, cx + 70, cy + 40), STROKE)
    # water lines
    for y in (1450, 1550, 1650):
        _line(d, [(300, y), (1740, y + 10 * math.sin(y))], STROKE_MED)
    _frame(d)
    return im


def scene_rose(seed: int) -> Image.Image:
    im, d = _new()
    cx, cy = 1024, 900
    for r in (80, 140, 200, 270, 340):
        _ellipse(d, (cx - r, cy - r * 0.85, cx + r, cy + r * 0.85), STROKE)
    # spiral suggestion
    pts = []
    for i in range(60):
        t = i / 59
        ang = t * 4 * math.pi
        rr = 40 + t * 280
        pts.append((cx + rr * math.cos(ang), cy + rr * 0.85 * math.sin(ang)))
    _line(d, pts, STROKE_MED)
    _line(d, [(cx, cy + 340), (cx, 1750)], STROKE)
    _poly(d, [(cx, 1400), (cx - 200, 1280), (cx - 40, 1450)])
    _poly(d, [(cx, 1550), (cx + 200, 1420), (cx + 40, 1580)])
    _frame(d)
    return im


def scene_potted_plant(seed: int) -> Image.Image:
    im, d = _new()
    # pot
    _poly(d, [(700, 1750), (1340, 1750), (1280, 1300), (760, 1300)])
    _poly(d, [(720, 1300), (1320, 1300), (1320, 1200), (720, 1200)])
    # leaves
    for i, a in enumerate((-50, -25, 0, 25, 50)):
        rad = math.radians(a - 90)
        x2 = 1024 + 420 * math.cos(rad)
        y2 = 1200 + 420 * math.sin(rad)
        _ellipse(d, (min(1024, x2) - 40, min(1200, y2) - 40, max(1024, x2) + 40, max(1200, y2) + 40), STROKE)
        _line(d, [(1024, 1200), (x2, y2)], STROKE_THIN)
    _frame(d)
    return im


def scene_hanging_basket(seed: int) -> Image.Image:
    im, d = _new()
    _line(d, [(1024, 200), (1024, 450)], STROKE)
    _ellipse(d, (720, 450, 1320, 750), STROKE)  # basket rim
    _poly(d, [(780, 650), (1260, 650), (1200, 1000), (840, 1000)])
    for x, y, r in ((700, 550, 70), (900, 480, 80), (1100, 470, 75), (1300, 560, 65), (850, 700, 60), (1150, 720, 70)):
        _flower(d, x, y, r)
    # trailing vines
    for x0 in (860, 1024, 1180):
        pts = [(x0, 1000)]
        for i in range(1, 8):
            pts.append((x0 + 40 * math.sin(i), 1000 + i * 80))
        _line(d, pts, STROKE_MED)
        _flower(d, pts[-1][0], pts[-1][1], 40)
    _frame(d)
    return im


def scene_wildflowers(seed: int) -> Image.Image:
    im, d = _new()
    _hill(d, 1600, 40, 1.0)
    for i in range(18):
        x = 250 + (i % 6) * 280 + (i // 6) * 40
        y = 700 + (i // 6) * 320
        _line(d, [(x, y + 200), (x, y)], STROKE_MED)
        _flower(d, x, y, 55 + (i % 3) * 10, petals=5 + i % 3)
    _frame(d)
    return im


# Mushrooms

def scene_mushroom_cluster(seed: int) -> Image.Image:
    im, d = _new()
    _hill(d, 1550, 50, 0.6)
    specs = [(600, 1400, 280), (950, 1450, 360), (1300, 1380, 240), (1550, 1480, 180), (400, 1500, 160)]
    for x, y, h in specs:
        _mushroom(d, x, y, h)
    _grass = [(p, 1600) for p in range(300, 1800, 40)]
    for x, y in _grass:
        _line(d, [(x, y), (x, y - 40 - (x % 30))], STROKE_THIN)
    _frame(d)
    return im


def scene_fairy_ring(seed: int) -> Image.Image:
    im, d = _new()
    cx, cy, R = 1024, 1100, 520
    for i in range(10):
        a = i * 36
        rad = math.radians(a)
        _mushroom(d, cx + R * math.cos(rad), cy + R * 0.55 * math.sin(rad), 140 + (i % 3) * 30)
    _flower(d, cx, cy, 90)
    _frame(d)
    return im


def scene_mushroom_house(seed: int) -> Image.Image:
    im, d = _new()
    # giant mushroom as house
    _poly(d, [(850, 1550), (1200, 1550), (1180, 1000), (870, 1000)])
    _ellipse(d, (600, 550, 1450, 1100), STROKE)
    for ox, oy, rr in ((-0.3, -0.1, 0.08), (0.1, -0.2, 0.1), (0.25, 0.05, 0.07), (-0.1, 0.1, 0.06)):
        _circle(d, 1025 + 400 * ox, 825 + 250 * oy, 400 * rr, STROKE_THIN)
    # door + window
    _poly(d, [(960, 1550), (1090, 1550), (1090, 1250), (960, 1250)])
    _circle(d, 1025, 1180, 18, STROKE_THIN)
    _ellipse(d, (1120, 1150, 1220, 1250), STROKE)
    _mushroom(d, 500, 1550, 180)
    _mushroom(d, 1550, 1580, 150)
    _frame(d)
    return im


def scene_mushroom_garden(seed: int) -> Image.Image:
    im, d = _new()
    _poly(d, [(300, 1600), (1750, 1600), (1700, 1300), (350, 1300)])  # bed
    for i, x in enumerate(range(450, 1650, 180)):
        _mushroom(d, x, 1280, 160 + (i % 4) * 40)
    for x in (400, 700, 1100, 1500):
        _flower(d, x, 1700, 50)
    _frame(d)
    return im


# Animals

def scene_chubby_bird(seed: int) -> Image.Image:
    im, d = _new()
    _bird(d, 900, 1000, 280)
    _ellipse(d, (700, 1400, 1300, 1550), STROKE)  # branch
    _line(d, [(850, 1280), (900, 1400)], STROKE_MED)
    _line(d, [(1000, 1280), (1050, 1400)], STROKE_MED)
    _flower(d, 400, 600, 80)
    _flower(d, 1600, 550, 70)
    _frame(d)
    return im


def scene_bunny(seed: int) -> Image.Image:
    im, d = _new()
    # body
    _ellipse(d, (550, 950, 1500, 1700), STROKE)
    # head
    _circle(d, 1024, 820, 260, STROKE)
    # ears (sit above head, not through eyes)
    _ellipse(d, (860, 180, 980, 720), STROKE)
    _ellipse(d, (1070, 180, 1190, 720), STROKE)
    _ellipse(d, (885, 260, 955, 620), STROKE_THIN)
    _ellipse(d, (1095, 260, 1165, 620), STROKE_THIN)
    # face
    _circle(d, 940, 800, 22, STROKE)
    _circle(d, 1110, 800, 22, STROKE)
    _ellipse(d, (990, 860, 1060, 910), STROKE)
    _line(d, [(1024, 910), (1024, 960)], STROKE_THIN)
    _line(d, [(950, 980), (1024, 960), (1100, 980)], STROKE_THIN)
    # paws
    _ellipse(d, (720, 1550, 900, 1700), STROKE)
    _ellipse(d, (1150, 1550, 1330, 1700), STROKE)
    # ground flowers for density
    for x, y, r in ((320, 1500, 80), (480, 1650, 60), (1600, 1480, 75), (1750, 1620, 55)):
        _flower(d, x, y, r)
    _mushroom(d, 300, 1200, 140)
    _frame(d)
    return im


def scene_snail(seed: int) -> Image.Image:
    im, d = _new()
    # shell spiral
    cx, cy = 1100, 1000
    _circle(d, cx, cy, 320, STROKE)
    _circle(d, cx, cy, 220, STROKE)
    _circle(d, cx, cy, 120, STROKE)
    pts = []
    for i in range(80):
        t = i / 79
        ang = t * 3 * math.pi
        rr = 40 + t * 280
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    _line(d, pts, STROKE_MED)
    # body
    _ellipse(d, (350, 1100, 1000, 1450), STROKE)
    # eyestalks
    _line(d, [(420, 1150), (380, 900)], STROKE)
    _line(d, [(500, 1120), (520, 880)], STROKE)
    _circle(d, 380, 880, 35, STROKE)
    _circle(d, 520, 860, 35, STROKE)
    _frame(d)
    return im


def scene_hedgehog(seed: int) -> Image.Image:
    im, d = _new()
    _ellipse(d, (500, 900, 1550, 1500), STROKE)
    # spines
    for i in range(16):
        a = 200 + i * 10
        rad = math.radians(a)
        x0 = 1025 + 400 * math.cos(rad)
        y0 = 1200 + 250 * math.sin(rad)
        x1 = 1025 + 580 * math.cos(rad)
        y1 = 1200 + 380 * math.sin(rad)
        _line(d, [(x0, y0), (x1, y1)], STROKE_MED)
    # face
    _ellipse(d, (520, 1100, 820, 1400), STROKE)
    _circle(d, 620, 1200, 16, STROKE)
    _circle(d, 720, 1200, 16, STROKE)
    _ellipse(d, (640, 1280, 700, 1320), STROKE)
    _mushroom(d, 1600, 1500, 160)
    _frame(d)
    return im


def scene_sleeping_fox(seed: int) -> Image.Image:
    im, d = _new()
    # curled body
    _ellipse(d, (500, 900, 1500, 1500), STROKE)
    _ellipse(d, (700, 1000, 1300, 1400), STROKE_MED)
    # head
    _circle(d, 700, 1050, 180, STROKE)
    _poly(d, [(580, 950), (620, 780), (700, 920)])  # ear
    _poly(d, [(700, 920), (780, 780), (820, 950)])
    # closed eyes
    _line(d, [(640, 1040), (690, 1060), (640, 1080)], STROKE_THIN)
    _line(d, [(740, 1040), (790, 1060), (740, 1080)], STROKE_THIN)
    # tail tip
    _ellipse(d, (1300, 1100, 1550, 1350), STROKE)
    _flower(d, 1600, 700, 80)
    _frame(d)
    return im


def scene_fishbowl(seed: int) -> Image.Image:
    im, d = _new()
    _ellipse(d, (500, 450, 1550, 1600), STROKE)
    _ellipse(d, (650, 420, 1400, 520), STROKE)  # rim
    # water line
    _line(d, [(560, 800), (1490, 800)], STROKE_MED)
    # fish
    _ellipse(d, (800, 1000, 1200, 1250), STROKE)
    _poly(d, [(800, 1125), (680, 1000), (680, 1250)])
    _circle(d, 1100, 1100, 20, STROKE)
    # plant
    for x in (600, 700):
        pts = [(x, 1500)]
        for i in range(1, 6):
            pts.append((x + 30 * math.sin(i), 1500 - i * 80))
        _line(d, pts, STROKE_MED)
    # bubbles
    for cx, cy, r in ((1300, 900, 25), (1350, 1000, 18), (1280, 1080, 12)):
        _circle(d, cx, cy, r, STROKE_THIN)
    _frame(d)
    return im


# Cozy objects

def scene_teapot(seed: int) -> Image.Image:
    im, d = _new()
    _ellipse(d, (550, 700, 1400, 1400), STROKE)
    _ellipse(d, (700, 600, 1250, 800), STROKE)  # lid
    _circle(d, 975, 620, 40, STROKE)
    # spout
    _poly(d, [(1400, 1000), (1700, 850), (1680, 950), (1400, 1100)])
    # handle
    pts = _arc_pts(550, 1050, 180, 90, 270, 30)
    _line(d, pts, STROKE)
    # cup
    _poly(d, [(1500, 1600), (1850, 1600), (1800, 1300), (1550, 1300)])
    pts = _arc_pts(1850, 1450, 80, -60, 60, 20)
    _line(d, pts, STROKE_MED)
    _flower(d, 400, 500, 70)
    _frame(d)
    return im


def scene_lantern(seed: int) -> Image.Image:
    im, d = _new()
    _line(d, [(1024, 250), (1024, 450)], STROKE)
    _poly(d, [(850, 450), (1200, 450), (1200, 550), (850, 550)])
    _poly(d, [(880, 550), (1170, 550), (1170, 1300), (880, 1300)])
    # panes
    _line(d, [(1025, 550), (1025, 1300)], STROKE_MED)
    _line(d, [(880, 925), (1170, 925)], STROKE_MED)
    # flame
    _ellipse(d, (980, 850, 1070, 1000), STROKE)
    _poly(d, [(900, 1300), (1150, 1300), (1200, 1450), (850, 1450)])
    _mushroom(d, 500, 1450, 180)
    _mushroom(d, 1550, 1480, 160)
    _frame(d)
    return im


def scene_cozy_window(seed: int) -> Image.Image:
    im, d = _new()
    _poly(d, [(400, 400), (1640, 400), (1640, 1600), (400, 1600)], STROKE)
    _line(d, [(1020, 400), (1020, 1600)], STROKE)
    _line(d, [(400, 1000), (1640, 1000)], STROKE)
    # curtains
    _poly(d, [(400, 400), (650, 400), (600, 1600), (400, 1600)])
    _poly(d, [(1640, 400), (1390, 400), (1440, 1600), (1640, 1600)])
    # scene outside: sun + hills
    _sun(d, 1300, 650, 60)
    _hill(d, 850, 30, 0.5)
    _tree(d, 750, 950, 140)
    # sill plant
    _poly(d, [(850, 1600), (1190, 1600), (1160, 1450), (880, 1450)])
    _flower(d, 1020, 1350, 55)
    _frame(d)
    return im


def scene_camp_tent(seed: int) -> Image.Image:
    im, d = _new()
    _sun(d, 1600, 350, 90)
    _poly(d, [(500, 1400), (1024, 600), (1550, 1400)])
    _line(d, [(1024, 600), (1024, 1400)], STROKE_MED)
    _poly(d, [(900, 1400), (1150, 1400), (1150, 1100), (900, 1100)])  # flap
    _tree(d, 300, 1300, 320)
    _tree(d, 1750, 1350, 280)
    # campfire
    _poly(d, [(700, 1600), (780, 1450), (860, 1600)])
    _poly(d, [(760, 1600), (840, 1430), (920, 1600)])
    _poly(d, [(820, 1600), (900, 1450), (980, 1600)])
    _frame(d)
    return im


def scene_stack_books(seed: int) -> Image.Image:
    im, d = _new()
    y = 1500
    for i, (w, h) in enumerate(((900, 140), (820, 120), (960, 150), (780, 110), (880, 130))):
        x = 1024 - w / 2 + (i % 3) * 20
        _poly(d, [(x, y), (x + w, y), (x + w, y - h), (x, y - h)])
        _line(d, [(x + 40, y - h / 2), (x + w - 40, y - h / 2)], STROKE_THIN)
        y -= h
    _mug = True
    _ellipse(d, (1450, 900, 1750, 1200), STROKE)
    _poly(d, [(1480, 1050), (1720, 1050), (1700, 1350), (1500, 1350)])
    pts = _arc_pts(1750, 1150, 70, -70, 70, 20)
    _line(d, pts, STROKE_MED)
    _flower(d, 400, 600, 80)
    _frame(d)
    return im


# Patterns

def scene_pattern_leaves(seed: int) -> Image.Image:
    im, d = _new()
    for row in range(5):
        for col in range(5):
            x = 280 + col * 360
            y = 280 + row * 360
            _ellipse(d, (x - 100, y - 160, x + 100, y + 160), STROKE)
            _line(d, [(x, y - 140), (x, y + 140)], STROKE_THIN)
            for k in (-2, -1, 1, 2):
                _line(d, [(x, y + k * 40), (x + 50 * (1 if k > 0 else -1), y + k * 40 - 20)], STROKE_THIN)
    _frame(d)
    return im


def scene_pattern_scallops(seed: int) -> Image.Image:
    im, d = _new()
    for row in range(8):
        y = 280 + row * 200
        pts = []
        for i in range(40):
            x = MARGIN + (SIZE - 2 * MARGIN) * i / 39
            yy = y + 70 * abs(math.sin(i / 39 * math.pi * 5))
            pts.append((x, yy))
        _line(d, pts, STROKE)
    _frame(d)
    return im


def scene_pattern_stars(seed: int) -> Image.Image:
    im, d = _new()

    def star(cx, cy, r):
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        _poly(d, pts, STROKE)

    positions = [(400, 400), (1024, 350), (1650, 420), (550, 900), (1024, 950), (1500, 900), (400, 1500), (1024, 1550), (1650, 1480), (750, 1200), (1300, 1250)]
    for i, (x, y) in enumerate(positions):
        star(x, y, 90 + (i % 3) * 30)
    _frame(d)
    return im


def scene_pattern_honeycomb(seed: int) -> Image.Image:
    im, d = _new()

    def hexagon(cx, cy, r):
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        _poly(d, pts, STROKE)

    r = 110
    for row in range(7):
        for col in range(6):
            x = 320 + col * r * 1.75 + (row % 2) * r * 0.875
            y = 300 + row * r * 1.5
            hexagon(x, y, r)
            if (row + col) % 3 == 0:
                _flower(d, x, y, 35)
    _frame(d)
    return im


def scene_pattern_diamonds(seed: int) -> Image.Image:
    im, d = _new()
    for row in range(6):
        for col in range(6):
            x = 300 + col * 280
            y = 300 + row * 280
            _poly(d, [(x, y - 110), (x + 110, y), (x, y + 110), (x - 110, y)], STROKE)
            _circle(d, x, y, 35, STROKE_THIN)
    _frame(d)
    return im


SCENES: list[tuple[str, callable]] = [
    ("mountain-lake", scene_mountain_lake),
    ("rolling-hills", scene_rolling_hills),
    ("cabin-woods", scene_cabin_woods),
    ("beach", scene_beach),
    ("waterfall", scene_waterfall),
    ("desert", scene_desert),
    ("lighthouse", scene_lighthouse),
    ("snowy-cabin", scene_snowy_cabin),
    ("meadow-path", scene_meadow_path),
    ("hot-air-balloon", scene_hot_air_balloon),
    ("island", scene_island),
    ("canyon", scene_canyon),
    ("sunflower", scene_sunflower),
    ("tulip-row", scene_tulip_row),
    ("daisy-field", scene_daisy_field),
    ("lotus", scene_lotus),
    ("rose", scene_rose),
    ("potted-plant", scene_potted_plant),
    ("hanging-basket", scene_hanging_basket),
    ("wildflowers", scene_wildflowers),
    ("mushroom-cluster", scene_mushroom_cluster),
    ("fairy-ring", scene_fairy_ring),
    ("mushroom-house", scene_mushroom_house),
    ("mushroom-garden", scene_mushroom_garden),
    ("chubby-bird", scene_chubby_bird),
    ("bunny", scene_bunny),
    ("snail", scene_snail),
    ("hedgehog", scene_hedgehog),
    ("sleeping-fox", scene_sleeping_fox),
    ("fishbowl", scene_fishbowl),
    ("teapot", scene_teapot),
    ("lantern", scene_lantern),
    ("cozy-window", scene_cozy_window),
    ("camp-tent", scene_camp_tent),
    ("stack-books", scene_stack_books),
    ("pattern-leaves", scene_pattern_leaves),
    ("pattern-scallops", scene_pattern_scallops),
    ("pattern-stars", scene_pattern_stars),
    ("pattern-honeycomb", scene_pattern_honeycomb),
    ("pattern-diamonds", scene_pattern_diamonds),
]


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "products" / "quiet-places-40" / "art-source"
    out.mkdir(parents=True, exist_ok=True)
    assert len(SCENES) == 40, len(SCENES)
    for i, (name, fn) in enumerate(SCENES, start=1):
        im = fn(seed=1000 + i)
        path = out / f"qp2-{i:02d}-{name}.png"
        im.save(path, optimize=True)
        print(f"wrote {path.name}")
    print(f"done: {len(SCENES)} pages -> {out}")


if __name__ == "__main__":
    main()
