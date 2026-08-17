#!/usr/bin/env python3
"""Convert illustrated scenes into clean bold black line art for Quiet Places.

Style rules (must match STYLE.md):
- Medium-bold outlines (not hairline, not marker-blob thick)
- Pure black lines on pure white — no gray, no solid black fills
- No text/letters on pages (source art must be text-free)
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "products" / "quiet-places-40" / "art-source"
SIZE = 2048

# Soft ink value (not pure 0) — prints cleaner, less “overly dark”
INK_VALUE = 28


def _to_ink_mask(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # Higher C → thinner strokes (fewer dark pixels counted as ink)
    thr = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 12
    )
    _, hard = cv2.threshold(blur, 85, 255, cv2.THRESH_BINARY)
    ink = ((thr < 128) | (hard < 128)).astype(np.uint8)

    # Speckle cleanup
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    # Hollow only true solid fills (eyes/centers), never stroke interiors.
    # dist>2 on medium strokes creates hollow “railroad” double-lines.
    dist = cv2.distanceTransform(ink, cv2.DIST_L2, 5)
    thick_core = (dist > 4.5).astype(np.uint8)
    if thick_core.any():
        ink = np.where(thick_core > 0, 0, ink).astype(np.uint8)

    # Light medium weight — one gentle dilate only if strokes are hairline
    if float(ink.mean()) < 0.07:
        ink = cv2.dilate(ink, np.ones((2, 2), np.uint8), iterations=1)

    # Drop dust
    num, labels, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    cleaned = np.zeros_like(ink)
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= 14:
            cleaned[labels == i] = 1
    return cleaned


def to_ink(path: Path, out: Path) -> None:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    arr = np.array(im)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    ink = _to_ink_mask(gray)
    black = float(ink.mean())

    out_arr = np.where(ink > 0, INK_VALUE, 255).astype(np.uint8)
    Image.fromarray(out_arr, mode="L").convert("RGB").save(out, optimize=True)
    print(f"{out.name}: black%={black * 100:.1f}")


def main() -> None:
    src_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/quiet-gen")
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("qp-gen-*.png"))
    if not files:
        raise SystemExit(f"No qp-gen-*.png in {src_dir}")
    for i, f in enumerate(files, start=1):
        to_ink(f, OUT / f"qp2-{i:02d}.png")
    print(f"wrote {len(files)} pages -> {OUT}")


if __name__ == "__main__":
    main()
