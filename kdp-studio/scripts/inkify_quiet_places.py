#!/usr/bin/env python3
"""Convert generated illustrations into clean bold black line art for Quiet Places."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "products" / "quiet-places-40" / "art-source"
SIZE = 2048


def to_ink(path: Path, out: Path) -> None:
    im = Image.open(path).convert("RGB")
    # Square crop center if needed
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    arr = np.array(im)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Prefer dark-line extraction: lines are darker than paper
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # Adaptive threshold keeps local line structure
    thr = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 8
    )
    # Also take strong global dark pixels (pupils, thick strokes)
    _, hard = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
    # Combine: black where either says ink
    ink = ((thr < 128) | (hard < 128)).astype(np.uint8)

    # Remove tiny speckles; keep bold strokes
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    # Light thicken for bold-and-easy marker-friendly lines
    ink = cv2.dilate(ink, np.ones((2, 2), np.uint8), iterations=1)

    # Force pure B/W RGB
    out_arr = np.where(ink > 0, 15, 255).astype(np.uint8)
    Image.fromarray(out_arr, mode="L").convert("RGB").save(out, optimize=True)
    black = float(ink.mean()) * 100
    print(f"{out.name}: black%={black:.1f}")


def main() -> None:
    src_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/cursor/artifacts/assets")
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("qp-gen-*.png"))
    if not files:
        raise SystemExit(f"No qp-gen-*.png in {src_dir}")
    for i, f in enumerate(files, start=1):
        to_ink(f, OUT / f"qp2-{i:02d}.png")
    print(f"wrote {len(files)} pages -> {OUT}")


if __name__ == "__main__":
    main()
