#!/usr/bin/env python3
"""Inkify bold-and-easy illustrated scenes (STYLE.md) into art-source PNGs.

Usage:
  python3 scripts/inkify_bold_easy.py --slug stained-glass-40 --src /tmp/gen/stained-glass --glob 'sg-gen-*.png' --out-prefix sg2
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SIZE = 2048
INK_VALUE = 28


def _to_ink_mask(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thr = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 12
    )
    _, hard = cv2.threshold(blur, 85, 255, cv2.THRESH_BINARY)
    ink = ((thr < 128) | (hard < 128)).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    dist = cv2.distanceTransform(ink, cv2.DIST_L2, 5)
    thick_core = (dist > 4.5).astype(np.uint8)
    if thick_core.any():
        ink = np.where(thick_core > 0, 0, ink).astype(np.uint8)
    if float(ink.mean()) < 0.07:
        ink = cv2.dilate(ink, np.ones((2, 2), np.uint8), iterations=1)
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
    gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    ink = _to_ink_mask(gray)
    black = float(ink.mean())
    out_arr = np.where(ink > 0, INK_VALUE, 255).astype(np.uint8)
    Image.fromarray(out_arr, mode="L").convert("RGB").save(out, optimize=True)
    print(f"{out.name}: black%={black * 100:.1f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--glob", default="*-gen-*.png")
    ap.add_argument("--out-prefix", required=True)
    args = ap.parse_args()
    out_dir = ROOT / "products" / args.slug / "art-source"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(args.src.glob(args.glob))
    if not files:
        raise SystemExit(f"No {args.glob} in {args.src}")
    for i, f in enumerate(files, start=1):
        to_ink(f, out_dir / f"{args.out_prefix}-{i:02d}.png")
    print(f"wrote {len(files)} -> {out_dir}")


if __name__ == "__main__":
    main()
