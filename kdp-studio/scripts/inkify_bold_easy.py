#!/usr/bin/env python3
"""Inkify bold-and-easy illustrated scenes (STYLE.md) into art-source PNGs.

Preserves illustrated soft edges and supersamples so 1024px gen stair-steps
don't become torn silhouettes at page resolution. Page placement must NOT
re-threshold — see art_import.py.

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
WORK = 4096  # 2× supersample for smooth curves from 1024 gens
INK = 18.0
PAPER = 255.0


def _soft_ink(gray: np.ndarray) -> np.ndarray:
    """Soft ink map that keeps AA and seals only true micro-gaps."""
    g = cv2.bilateralFilter(gray, d=5, sigmaColor=28, sigmaSpace=28).astype(np.float32)

    t_lo, t_hi = 95.0, 175.0
    alpha = np.clip((t_hi - g) / (t_hi - t_lo), 0.0, 1.0)

    seed = (alpha >= 0.45).astype(np.uint8)
    sealed = cv2.morphologyEx(
        seed,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        iterations=2,
    )
    sealed = cv2.morphologyEx(
        sealed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)),
        iterations=1,
    )
    added = (sealed == 1) & (seed == 0)
    if np.any(added):
        dist = cv2.distanceTransform((1 - sealed).astype(np.uint8), cv2.DIST_L2, 5)
        join = np.clip(1.0 - dist / 2.2, 0.0, 1.0)
        alpha = np.where(added, np.maximum(alpha, join * 0.95), alpha)

    # Smooth silhouette at work resolution (kills gen pixel stair-steps)
    alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), sigmaX=1.1)
    alpha = np.clip(alpha, 0.0, 1.0)

    tone = PAPER - alpha * (PAPER - INK)
    # Solid near-black cores for print; fringe midtones remain for AA
    tone = np.where(alpha >= 0.88, INK, tone)
    tone = np.clip(tone, 0, 255)
    # Keep a short soft ramp (enough for smooth curves) but limit gray
    # levels so print PDFs stay well under GitHub's 100MB file cap.
    aa_steps = 12
    step = 255.0 / aa_steps
    tone = np.round(tone / step) * step
    return np.clip(tone, 0, 255).astype(np.uint8)


def to_ink(path: Path, out: Path) -> None:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((WORK, WORK), Image.Resampling.LANCZOS)
    gray = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    page_hi = _soft_ink(gray)
    # AREA downsample = proper supersample AA
    page = cv2.resize(page_hi, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    black = float((page < 200).mean())
    Image.fromarray(page, mode="L").convert("RGB").save(out, optimize=True)
    print(f"{out.name}: ink%={black * 100:.1f}")


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
