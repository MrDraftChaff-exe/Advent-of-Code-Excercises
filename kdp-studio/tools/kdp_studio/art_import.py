"""Normalize external/AI line-art into KDP page PNGs.

Keeps the current colorable line weight, then cleans jagged stair-step edges
with signed-distance silhouette rounding and blur-downsample anti-aliasing.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .specs import trim_box


def _to_ink(gray: np.ndarray, threshold: int = 185) -> np.ndarray:
    return (gray < threshold).astype(np.uint8)


def _from_ink(ink: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(ink > 0, 0, 255).astype(np.uint8), mode="L")


def _lighten_overthick(ink: np.ndarray) -> np.ndarray:
    """If source strokes are already very heavy, thin them slightly first."""
    frac = float(ink.mean())
    if frac < 0.10:
        return ink
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thinned = cv2.erode(ink, k, iterations=1 if frac < 0.16 else 2)
    if thinned.mean() < 0.02:
        return ink
    return thinned


def _bridge_small_gaps(ink: np.ndarray, *, close_px: int = 5) -> np.ndarray:
    size = max(3, close_px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k, iterations=1)


def _fill_tiny_holes(ink: np.ndarray, *, max_hole: int = 24) -> np.ndarray:
    white = (1 - ink).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=8)
    out = ink.copy()
    h, w = ink.shape
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area > max_hole or area < 1:
            continue
        ys, xs = np.where(labels == i)
        if ys.min() == 0 or xs.min() == 0 or ys.max() == h - 1 or xs.max() == w - 1:
            continue
        out[labels == i] = 1
    return out


def _gentle_thicken(ink: np.ndarray, *, px: int = 2) -> np.ndarray:
    size = max(3, px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.dilate(ink, k, iterations=1)


def _smooth_mask_edges(ink: np.ndarray, *, sigma: float = 1.6, upscale: int = 2) -> np.ndarray:
    """Round stair-step edges without heavy thickening."""
    h, w = ink.shape
    up = cv2.resize(
        ink.astype(np.float32),
        (w * upscale, h * upscale),
        interpolation=cv2.INTER_LINEAR,
    )
    blurred = cv2.GaussianBlur(up, (0, 0), sigmaX=sigma * upscale, sigmaY=sigma * upscale)
    binary = (blurred >= 0.42).astype(np.float32)
    down = cv2.resize(binary, (w, h), interpolation=cv2.INTER_AREA)
    return (down >= 0.50).astype(np.uint8)


def _sdf_round_edges(ink: np.ndarray, *, sigma: float = 2.2) -> np.ndarray:
    """Round jagged silhouettes by blurring the signed-distance field.

    Re-thresholds at zero so stroke cores stay solid black — only the outline
    geometry is smoothed, not the fill.
    """
    dist_out = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 5)
    dist_in = cv2.distanceTransform(ink.astype(np.uint8), cv2.DIST_L2, 5)
    sdf = (dist_out - dist_in).astype(np.float32)
    sdf = cv2.GaussianBlur(sdf, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return (sdf < 0.0).astype(np.uint8)


def _anti_alias_edges(ink: np.ndarray, *, upscale: int = 4, sigma: float = 0.95) -> np.ndarray:
    """Return grayscale page (0=ink, 255=paper) with a rich soft edge ramp.

    Upscale → blur → area-downsample produces a smooth coverage ramp instead of
    a 1–2 level fringe that still looks stair-stepped in preview/print.
    """
    h, w = ink.shape
    up = cv2.resize(
        ink.astype(np.float32),
        (w * upscale, h * upscale),
        interpolation=cv2.INTER_NEAREST,
    )
    soft = cv2.GaussianBlur(up, (0, 0), sigmaX=sigma * upscale, sigmaY=sigma * upscale)
    down = cv2.resize(soft, (w, h), interpolation=cv2.INTER_AREA)
    return np.clip((1.0 - down) * 255.0, 0, 255).astype(np.uint8)


def prepare_line_art(gray: Image.Image) -> Image.Image:
    """Colorable weight + cleaned edges."""
    arr = np.array(gray.convert("L"))
    soft = cv2.GaussianBlur(arr, (5, 5), 0)
    ink = _to_ink(soft, threshold=178)
    ink = _lighten_overthick(ink)
    ink = _bridge_small_gaps(ink, close_px=5)
    ink = _fill_tiny_holes(ink, max_hole=20)

    # Establish colorable stroke weight, then round and anti-alias edges
    ink = _smooth_mask_edges(ink, sigma=2.2, upscale=3)
    ink = _gentle_thicken(ink, px=2)
    ink = _smooth_mask_edges(ink, sigma=1.5, upscale=3)
    ink = _fill_tiny_holes(ink, max_hole=16)
    ink = _bridge_small_gaps(ink, close_px=3)
    ink = _sdf_round_edges(ink, sigma=2.2)
    return Image.fromarray(_anti_alias_edges(ink, upscale=4, sigma=0.95), mode="L")


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
    fitted = ImageOps.contain(im, inner, Image.Resampling.LANCZOS)
    page_art = prepare_line_art(ImageOps.grayscale(fitted))

    canvas = Image.new("L", (canvas_w, canvas_h), 255)
    canvas.paste(page_art, ((canvas_w - page_art.width) // 2, (canvas_h - page_art.height) // 2))
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
    for old in pages_dir.glob("page-*.png"):
        old.unlink()
    for i, src in enumerate(files, start=1):
        out = pages_dir / f"page-{i:02d}.png"
        normalize_to_page(src, out, trim=trim, dpi=dpi, margin_in=margin_in)
        paths.append(out)
    return paths


def close_line_gaps(gray: Image.Image, *, close_px: int = 5, use_skeleton: bool = False) -> Image.Image:
    arr = np.array(gray.convert("L"))
    ink = _to_ink(arr)
    ink = _bridge_small_gaps(ink, close_px=close_px)
    ink = _smooth_mask_edges(ink, sigma=1.5, upscale=2)
    ink = _fill_tiny_holes(ink, max_hole=20)
    if close_px >= 5:
        ink = _gentle_thicken(ink, px=2)
    return _from_ink(ink)
