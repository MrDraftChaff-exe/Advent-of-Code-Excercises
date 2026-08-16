"""Normalize external/AI line-art into KDP page PNGs.

Goal: smooth, colorable outlines — sealed enough to avoid tears, but not so
thick/blocky that white regions disappear.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

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
    # One light erode for heavy AI fills so pages stay colorable
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thinned = cv2.erode(ink, k, iterations=1 if frac < 0.16 else 2)
    # Don't erase the drawing entirely
    if thinned.mean() < 0.02:
        return ink
    return thinned


def _bridge_small_gaps(ink: np.ndarray, *, close_px: int = 5) -> np.ndarray:
    """Light morphological close — only micro gaps, preserves open color areas."""
    size = max(3, close_px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k, iterations=1)


def _fill_tiny_holes(ink: np.ndarray, *, max_hole: int = 24) -> np.ndarray:
    """Fill only tiny white speckles inside strokes (not colorable pockets)."""
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
    """Slight thicken for print without blocky blobs."""
    size = max(3, px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.dilate(ink, k, iterations=1)


def prepare_line_art(gray: Image.Image) -> Image.Image:
    """Clean line art at whatever resolution it currently is."""
    arr = np.array(gray.convert("L"))
    # Mild blur before threshold reduces jagged stair-steps from AI rasters
    soft = cv2.GaussianBlur(arr, (3, 3), 0)
    ink = _to_ink(soft, threshold=180)
    ink = _lighten_overthick(ink)
    ink = _bridge_small_gaps(ink, close_px=5)
    ink = _fill_tiny_holes(ink, max_hole=20)
    ink = _gentle_thicken(ink, px=2)
    ink = _fill_tiny_holes(ink, max_hole=16)
    return _from_ink(ink)


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

    # Upscale smoothly FIRST so curves stay smooth (NEAREST made lines blocky)
    im = Image.open(src).convert("RGB")
    fitted = ImageOps.contain(im, inner, Image.Resampling.LANCZOS)
    # Slight unsharp after upscale to keep edges crisp before threshold
    fitted = fitted.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))

    gray = ImageOps.grayscale(fitted)
    page_art = prepare_line_art(gray)

    # One light page-scale seal for leftover micro gaps after upscale
    arr = np.array(page_art)
    ink = _to_ink(arr, threshold=200)
    ink = _bridge_small_gaps(ink, close_px=3)
    ink = _fill_tiny_holes(ink, max_hole=12)
    page_art = _from_ink(ink)

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


# Back-compat alias used by older call sites / experiments
def close_line_gaps(gray: Image.Image, *, close_px: int = 5, use_skeleton: bool = False) -> Image.Image:
    arr = np.array(gray.convert("L"))
    ink = _to_ink(arr)
    ink = _bridge_small_gaps(ink, close_px=close_px)
    ink = _fill_tiny_holes(ink, max_hole=20)
    if close_px >= 5:
        ink = _gentle_thicken(ink, px=2)
    return _from_ink(ink)
