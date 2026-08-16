"""Normalize external/AI line-art into KDP page PNGs with gap closing."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .specs import trim_box


def _bridge_endpoints(ink: np.ndarray, *, max_dist: int = 48) -> np.ndarray:
    """Connect nearby open stroke ends with short black segments.

    Finds pixels that look like line endpoints (few ink neighbors) and draws
    a thick line between pairs that are close enough. This seals the larger
    AI outline breaks that morphological close alone misses.
    """
    # Slight dilate so endpoints are easier to detect on thin strokes
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fat = cv2.dilate(ink, k, iterations=1)

    # Neighbor count via convolution on binary ink
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
    neighbors = cv2.filter2D(fat, -1, kernel)
    ys, xs = np.where((fat > 0) & (neighbors <= 2))
    if len(xs) < 2:
        return ink

    # Cap endpoints to keep this fast on large pages
    if len(xs) > 800:
        step = len(xs) // 800
        xs = xs[::step]
        ys = ys[::step]

    pts = np.column_stack((xs.astype(np.float32), ys.astype(np.float32)))
    out = ink.copy()
    used = set()
    max_d2 = float(max_dist * max_dist)

    # Greedy nearest-neighbor matching
    for i, p in enumerate(pts):
        if i in used:
            continue
        best_j = -1
        best_d2 = max_d2
        for j in range(i + 1, len(pts)):
            if j in used:
                continue
            d2 = float((p[0] - pts[j][0]) ** 2 + (p[1] - pts[j][1]) ** 2)
            if d2 < best_d2 and d2 > 4:  # skip same-pixel / adjacent
                best_d2 = d2
                best_j = j
        if best_j >= 0:
            used.add(i)
            used.add(best_j)
            a = (int(pts[i][0]), int(pts[i][1]))
            b = (int(pts[best_j][0]), int(pts[best_j][1]))
            cv2.line(out, a, b, 1, thickness=3, lineType=cv2.LINE_AA)
    return out


def close_line_gaps(gray: Image.Image, *, close_px: int = 15) -> Image.Image:
    """Bridge broken outlines in black line art on white."""
    arr = np.array(gray.convert("L"))
    ink = (arr < 200).astype(np.uint8)

    size = max(3, close_px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k, iterations=2)

    # Seal larger outline breaks by bridging nearby stroke ends
    closed = _bridge_endpoints(closed, max_dist=max(36, close_px * 3))

    # Thicken for marker-friendly print lines (also seals leftover micro-gaps)
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.dilate(closed, k2, iterations=1)

    out = np.where(closed > 0, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="L")


def normalize_to_page(
    src: Path,
    out: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> Path:
    width_in, height_in = trim_box(trim)
    canvas_w = int(round(width_in * dpi))
    canvas_h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    inner = (canvas_w - 2 * margin, canvas_h - 2 * margin)

    im = Image.open(src).convert("RGB")
    # Close on source first (gaps are fewer px), then again at print scale.
    g0 = ImageOps.grayscale(im)
    bw0 = g0.point(lambda p: 0 if p < 190 else 255)
    bw0 = close_line_gaps(bw0, close_px=11)

    fitted = ImageOps.contain(bw0.convert("RGB"), inner, Image.Resampling.NEAREST)
    g = fitted.convert("L")
    bw = g.point(lambda p: 0 if p < 190 else 255)
    bw = close_line_gaps(bw, close_px=17)

    canvas = Image.new("L", (canvas_w, canvas_h), 255)
    canvas.paste(bw, ((canvas_w - bw.width) // 2, (canvas_h - bw.height) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, dpi=(dpi, dpi))
    return out


def import_art_folder(
    art_dir: Path,
    pages_dir: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> list[Path]:
    files = sorted(art_dir.glob("*.png")) + sorted(art_dir.glob("*.jpg"))
    if not files:
        raise FileNotFoundError(f"No images in {art_dir}")
    paths: list[Path] = []
    pages_dir.mkdir(parents=True, exist_ok=True)
    # Clear old pages so renumbers stay clean
    for old in pages_dir.glob("page-*.png"):
        old.unlink()
    for i, src in enumerate(files, start=1):
        out = pages_dir / f"page-{i:02d}.png"
        normalize_to_page(src, out, trim=trim, dpi=dpi, margin_in=margin_in)
        paths.append(out)
    return paths
