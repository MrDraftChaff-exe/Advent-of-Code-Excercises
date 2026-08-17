"""Normalize external/AI line-art into KDP page PNGs.

Builds a colorable ink weight, then vector-traces (potrace) and re-rasterizes
with anti-aliasing so printed curves stay smooth — no stair-step roughness.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from potrace import BezierSegment, Bitmap, CornerSegment

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


def _sdf_round_edges(ink: np.ndarray, *, sigma: float = 5.5) -> np.ndarray:
    """Round jagged silhouettes before vector tracing."""
    dist_out = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 5)
    dist_in = cv2.distanceTransform(ink.astype(np.uint8), cv2.DIST_L2, 5)
    sdf = (dist_out - dist_in).astype(np.float32)
    sdf = cv2.GaussianBlur(sdf, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return (sdf < 0.0).astype(np.uint8)


def _pt(p) -> np.ndarray:
    return np.array([float(p.x), float(p.y)], dtype=np.float64)


def _curve_to_polygon(curve, *, samples: int = 18) -> np.ndarray | None:
    """Sample potrace Bezier/corner segments into a dense polygon."""
    pts: list[list[float]] = []
    cur = _pt(curve.start_point)
    for seg in curve.segments:
        if isinstance(seg, BezierSegment):
            c1, c2, end = _pt(seg.c1), _pt(seg.c2), _pt(seg.end_point)
            t = np.linspace(0.0, 1.0, samples)[:, None]
            bez = (
                (1 - t) ** 3 * cur
                + 3 * (1 - t) ** 2 * t * c1
                + 3 * (1 - t) * t**2 * c2
                + t**3 * end
            )
            pts.extend(bez[:-1].tolist())
            cur = end
        elif isinstance(seg, CornerSegment):
            # Soften sharp corners so raster edges don't look bitten
            corner, end = _pt(seg.c), _pt(seg.end_point)
            mid1 = 0.65 * cur + 0.35 * corner
            mid2 = 0.35 * corner + 0.65 * end
            pts.append(mid1.tolist())
            pts.append(mid2.tolist())
            pts.append(end.tolist())
            cur = end
        else:
            end = _pt(getattr(seg, "end_point"))
            pts.append(end.tolist())
            cur = end
    if len(pts) < 3:
        return None
    return np.asarray(pts, dtype=np.float64)


def _signed_area(poly: np.ndarray) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _vector_smooth_raster(
    ink: np.ndarray,
    *,
    scale: int = 6,
    opttolerance: float = 0.8,
    alphamax: float = 1.334,
    aa_sigma: float = 0.95,
) -> np.ndarray:
    """Trace ink to smooth Beziers, then supersample + downsample for AA gray page."""
    h, w = ink.shape
    if ink.mean() < 0.001:
        return np.full((h, w), 255, dtype=np.uint8)

    path = Bitmap(ink.astype(bool)).trace(
        turdsize=5,
        opttolerance=opttolerance,
        alphamax=alphamax,
    )
    full = float(w * h)
    polys: list[np.ndarray] = []
    for curve in path:
        poly = _curve_to_polygon(curve)
        if poly is None:
            continue
        # Potrace sometimes emits a full-frame background path — skip it
        if abs(_signed_area(poly)) > 0.80 * full:
            continue
        polys.append(poly)

    if not polys:
        # Fallback: soft AA of the binary mask
        return _anti_alias_mask(ink, upscale=scale, sigma=aa_sigma)

    polys.sort(key=lambda p: abs(_signed_area(p)), reverse=True)
    canvas = np.zeros((h * scale, w * scale), dtype=np.uint8)
    layer = np.zeros_like(canvas)
    for poly in polys:
        layer.fill(0)
        cv2.fillPoly(layer, [(poly * scale).astype(np.int32)], 1)
        np.bitwise_xor(canvas, layer, out=canvas)

    soft = cv2.GaussianBlur(canvas.astype(np.float32), (0, 0), sigmaX=aa_sigma)
    down = cv2.resize(soft, (w, h), interpolation=cv2.INTER_AREA)
    return np.clip((1.0 - down) * 255.0, 0, 255).astype(np.uint8)


def _anti_alias_mask(ink: np.ndarray, *, upscale: int = 4, sigma: float = 0.95) -> np.ndarray:
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
    """Colorable weight, then vector-smooth re-raster with anti-aliased edges."""
    arr = np.array(gray.convert("L"))
    soft = cv2.GaussianBlur(arr, (5, 5), 0)
    ink = _to_ink(soft, threshold=178)
    ink = _lighten_overthick(ink)
    ink = _bridge_small_gaps(ink, close_px=5)
    ink = _fill_tiny_holes(ink, max_hole=20)

    # Establish the approved colorable stroke weight
    ink = _smooth_mask_edges(ink, sigma=2.2, upscale=3)
    ink = _gentle_thicken(ink, px=2)
    ink = _smooth_mask_edges(ink, sigma=1.5, upscale=3)
    ink = _fill_tiny_holes(ink, max_hole=16)
    ink = _bridge_small_gaps(ink, close_px=3)

    # Round jagged raster geometry, then vector-trace + AA re-rasterize
    ink = _sdf_round_edges(ink, sigma=5.5)
    return Image.fromarray(_vector_smooth_raster(ink), mode="L")


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
