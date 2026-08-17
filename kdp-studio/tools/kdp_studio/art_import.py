"""Normalize external/AI line-art into KDP page PNGs + SVGs.

Builds a colorable ink weight, vector-traces with potrace, writes:
  - page-XX.svg  — true vectors for Preview + print PDF
  - page-XX.png  — Cairo-rasterized preview/fallback
"""

from __future__ import annotations

import io
from pathlib import Path

import cairosvg
import cv2
import numpy as np
from PIL import Image, ImageOps
from potrace import BezierSegment, Bitmap, CornerSegment

from .specs import trim_box

Image.MAX_IMAGE_PIXELS = None


def _to_ink(gray: np.ndarray, threshold: int = 185) -> np.ndarray:
    return (gray < threshold).astype(np.uint8)


def _from_ink(ink: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(ink > 0, 0, 255).astype(np.uint8), mode="L")


def _lighten_overthick(ink: np.ndarray) -> np.ndarray:
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


def _sdf_round_edges(ink: np.ndarray, *, sigma: float = 6.5) -> np.ndarray:
    target = float(ink.mean())
    dist_out = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 5)
    dist_in = cv2.distanceTransform(ink.astype(np.uint8), cv2.DIST_L2, 5)
    sdf = cv2.GaussianBlur((dist_out - dist_in).astype(np.float32), (0, 0), sigmaX=sigma)
    lo, hi = -4.0, 8.0
    for _ in range(20):
        tau = 0.5 * (lo + hi)
        if float((sdf < tau).mean()) > target:
            hi = tau
        else:
            lo = tau
    return (sdf < 0.5 * (lo + hi)).astype(np.uint8)


def _curve_bbox(curve) -> tuple[float, float, float, float]:
    xs = [float(curve.start_point.x)]
    ys = [float(curve.start_point.y)]
    for seg in curve.segments:
        pts = (seg.c1, seg.c2, seg.end_point) if isinstance(seg, BezierSegment) else (seg.c, seg.end_point)
        for p in pts:
            xs.append(float(p.x))
            ys.append(float(p.y))
    return min(xs), min(ys), max(xs), max(ys)


def _curve_to_svg_d(curve, *, dx: float = 0.0, dy: float = 0.0) -> str:
    def t(p) -> tuple[float, float]:
        return float(p.x) + dx, float(p.y) + dy

    x0, y0 = t(curve.start_point)
    parts = [f"M {x0:.3f} {y0:.3f}"]
    for seg in curve.segments:
        if isinstance(seg, BezierSegment):
            c1 = t(seg.c1)
            c2 = t(seg.c2)
            end = t(seg.end_point)
            parts.append(f"C {c1[0]:.3f} {c1[1]:.3f} {c2[0]:.3f} {c2[1]:.3f} {end[0]:.3f} {end[1]:.3f}")
        elif isinstance(seg, CornerSegment):
            c = t(seg.c)
            end = t(seg.end_point)
            parts.append(f"Q {c[0]:.3f} {c[1]:.3f} {end[0]:.3f} {end[1]:.3f}")
        else:
            end = t(seg.end_point)
            parts.append(f"L {end[0]:.3f} {end[1]:.3f}")
    parts.append("Z")
    return " ".join(parts)


def _trace_curves(ink: np.ndarray, *, opttolerance: float = 1.0):
    h, w = ink.shape
    path = Bitmap(ink.astype(bool)).trace(
        turdsize=5,
        opttolerance=opttolerance,
        alphamax=1.334,
    )
    curves = []
    for curve in path:
        x0, y0, x1, y1 = _curve_bbox(curve)
        bw, bh = x1 - x0, y1 - y0
        # Skip full-frame / near-full-page paths — even-odd fill turns them into
        # solid black backgrounds (unacceptable for coloring pages).
        touches = x0 <= 2 and y0 <= 2 and x1 >= w - 3 and y1 >= h - 3
        if touches and bw >= w * 0.98 and bh >= h * 0.98:
            continue
        if bw >= w * 0.85 and bh >= h * 0.85:
            continue
        curves.append(curve)
    return curves


def build_page_svg(
    ink: np.ndarray,
    *,
    canvas_w: int,
    canvas_h: int,
    offset: tuple[int, int],
    opttolerance: float = 1.0,
) -> str:
    """Full-page SVG (white canvas + even-odd black art)."""
    ox, oy = offset
    curves = _trace_curves(ink, opttolerance=opttolerance)
    d = " ".join(_curve_to_svg_d(c, dx=ox, dy=oy) for c in curves)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" shape-rendering="geometricPrecision">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<path fill="#000000" fill-rule="evenodd" d="{d}"/>'
        f"</svg>\n"
    )


def rasterize_svg(svg: str, *, width: int, height: int, scale: int = 2) -> Image.Image:
    png = cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        output_width=max(1, width * scale),
        output_height=max(1, height * scale),
    )
    im = Image.open(io.BytesIO(png)).convert("L")
    if scale != 1:
        im = im.resize((width, height), Image.Resampling.LANCZOS)
    arr = np.array(im).astype(np.float32)
    arr = np.where(arr < 28, 0.0, arr)
    arr = np.where(arr > 242, 255.0, arr)
    return Image.fromarray(arr.astype(np.uint8), mode="L")


def _build_ink_mask(gray: Image.Image) -> np.ndarray:
    arr = np.array(gray.convert("L"))
    soft = cv2.GaussianBlur(arr, (5, 5), 0)
    ink = _to_ink(soft, threshold=178)
    ink = _lighten_overthick(ink)
    ink = _bridge_small_gaps(ink, close_px=5)
    ink = _fill_tiny_holes(ink, max_hole=20)
    ink = _smooth_mask_edges(ink, sigma=2.2, upscale=3)
    ink = _gentle_thicken(ink, px=2)
    ink = _smooth_mask_edges(ink, sigma=1.5, upscale=3)
    ink = _fill_tiny_holes(ink, max_hole=16)
    ink = _bridge_small_gaps(ink, close_px=3)
    return _sdf_round_edges(ink, sigma=6.5)


def _crop_to_ink(im: Image.Image, *, pad_frac: float = 0.04, threshold: int = 200) -> Image.Image:
    """Remove empty source padding so the subject can scale up on the page."""
    gray = ImageOps.grayscale(im)
    arr = np.array(gray)
    ink = arr < threshold
    if not np.any(ink):
        return im
    ys, xs = np.where(ink)
    h, w = arr.shape
    pad = max(8, int(round(pad_frac * max(w, h))))
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(w, int(xs.max()) + pad + 1)
    y1 = min(h, int(ys.max()) + pad + 1)
    return im.crop((x0, y0, x1, y1))


def _draw_closed_poly(canvas: np.ndarray, pts: list[tuple[int, int]], width: int = 6) -> None:
    arr = np.array(pts, dtype=np.int32).reshape(-1, 1, 2)
    cv2.polylines(canvas, [arr], isClosed=True, color=1, thickness=max(3, width), lineType=cv2.LINE_AA)


def _draw_ring(canvas: np.ndarray, cx: int, cy: int, r: int, width: int = 6) -> None:
    cv2.circle(canvas, (cx, cy), r, 1, thickness=max(3, width), lineType=cv2.LINE_AA)


def _motif_clearance_ok(page: np.ndarray, cx: int, cy: int, r: int, pad: int = 18) -> bool:
    h, w = page.shape
    y_a, y_b = max(0, cy - r - pad), min(h, cy + r + pad)
    x_a, x_b = max(0, cx - r - pad), min(w, cx + r + pad)
    return page[y_a:y_b, x_a:x_b].mean() <= 0.015


def _draw_motif(page: np.ndarray, cx: int, cy: int, r: int, kind: int) -> None:
    if kind == 0:
        _draw_ring(page, cx, cy, r, width=7)
        _draw_ring(page, cx, cy, max(12, r // 3), width=6)
    elif kind == 1:
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        _draw_closed_poly(page, pts, width=7)
        _draw_ring(page, cx, cy, max(10, r // 4), width=5)
    elif kind == 2:
        petals = []
        for k in range(5):
            ang = -np.pi / 2 + k * 2 * np.pi / 5
            petals.append((int(cx + r * np.cos(ang)), int(cy + r * np.sin(ang))))
        _draw_closed_poly(page, petals, width=7)
        _draw_ring(page, cx, cy, max(10, r // 4), width=5)
    else:
        # Nested hexagon — extra closed regions to color
        for scale, width in ((1.0, 7), (0.55, 6)):
            rr = max(12, int(r * scale))
            pts = []
            for k in range(6):
                ang = np.pi / 6 + k * np.pi / 3
                pts.append((int(cx + rr * np.cos(ang)), int(cy + rr * np.sin(ang))))
            _draw_closed_poly(page, pts, width=width)


def _fill_band_with_motifs(
    page: np.ndarray,
    *,
    bx0: int,
    by0: int,
    bx1: int,
    by1: int,
    rng: np.random.Generator,
) -> None:
    """Pack medium/large closed shapes into an empty rectangle."""
    bw, bh = bx1 - bx0, by1 - by0
    if bw < 100 or bh < 90:
        return
    # Larger companions in a short grid — fill the band without sticker-sheet clutter
    r_hi = max(48, min(120, int(bh * 0.42), int(bw * 0.14)))
    r_lo = max(36, int(r_hi * 0.7))
    cols = max(2, min(4, bw // max(140, r_hi * 2 + 40)))
    rows = max(1, min(3, bh // max(120, r_hi * 2 + 36)))
    for row in range(rows):
        for col in range(cols):
            cx = int(bx0 + (col + 0.5) * bw / cols + rng.integers(-22, 23))
            cy = int(by0 + (row + 0.5) * bh / rows + rng.integers(-18, 19))
            r = int(rng.integers(r_lo, r_hi + 1))
            cx = int(np.clip(cx, bx0 + r + 10, bx1 - r - 10))
            cy = int(np.clip(cy, by0 + r + 10, by1 - r - 10))
            if not _motif_clearance_ok(page, cx, cy, r, pad=22):
                continue
            _draw_motif(page, cx, cy, r, int(rng.integers(0, 4)))


def _enrich_sparse_canvas(
    ink: np.ndarray,
    *,
    canvas_w: int,
    canvas_h: int,
    ox: int,
    oy: int,
    seed: int,
    min_fill: float = 0.72,
) -> np.ndarray:
    """If the subject leaves large empty bands, add extra closed shapes to color.

    Companion motifs only — never a page-sized frame (those become solid black
    under even-odd vector fill). Returns a full-page ink mask (1=ink).
    """
    page = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    h, w = ink.shape
    page[oy : oy + h, ox : ox + w] = ink

    ys, xs = np.where(page > 0)
    if ys.size == 0:
        return page
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    fill_h = (y1 - y0 + 1) / canvas_h
    fill_w = (x1 - x0 + 1) / canvas_w
    if fill_h >= min_fill and fill_w >= min_fill:
        return page

    rng = np.random.default_rng(seed)
    pad = max(48, min(x0, canvas_w - 1 - x1, y0, canvas_h - 1 - y1, 120))
    bands: list[tuple[int, int, int, int]] = []
    top_gap = y0 - pad
    bot_gap = (canvas_h - 1 - pad) - y1
    left_gap = x0 - pad
    right_gap = (canvas_w - 1 - pad) - x1
    if top_gap > 110:
        bands.append((pad, pad, canvas_w - pad, y0 - 28))
    if bot_gap > 110:
        bands.append((pad, y1 + 28, canvas_w - pad, canvas_h - pad))
    if fill_w < 0.62 and left_gap > 120:
        bands.append((pad, max(pad, y0), x0 - 28, min(canvas_h - pad, y1)))
    if fill_w < 0.62 and right_gap > 120:
        bands.append((x1 + 28, max(pad, y0), canvas_w - pad, min(canvas_h - pad, y1)))

    for bx0, by0, bx1, by1 in bands:
        _fill_band_with_motifs(page, bx0=bx0, by0=by0, bx1=bx1, by1=by1, rng=rng)

    return page


def prepare_line_art(gray: Image.Image) -> Image.Image:
    """Fallback raster-only helper (prefer normalize_to_page for SVG+PNG)."""
    ink = _build_ink_mask(gray)
    h, w = ink.shape
    svg = build_page_svg(ink, canvas_w=w, canvas_h=h, offset=(0, 0))
    return rasterize_svg(svg, width=w, height=h, scale=2)


def normalize_to_page(
    src: Path,
    out: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.375,
    page_index: int = 1,
) -> Path:
    """Place art large on the page; add extra colorable shapes if still sparse."""
    width_in, height_in = trim_box(trim)
    canvas_w = int(round(width_in * dpi))
    canvas_h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    inner = (canvas_w - 2 * margin, canvas_h - 2 * margin)

    im = Image.open(src).convert("RGB")
    im = _crop_to_ink(im)
    fitted = ImageOps.contain(im, inner, Image.Resampling.LANCZOS)
    ink = _build_ink_mask(ImageOps.grayscale(fitted))
    ox = (canvas_w - ink.shape[1]) // 2
    # Short/wide art: pin toward the top so one large companion band fills below
    subject_fill_h = ink.shape[0] / canvas_h
    if subject_fill_h < 0.68:
        oy = margin + max(0, int(round((inner[1] - ink.shape[0]) * 0.12)))
    else:
        oy = (canvas_h - ink.shape[0]) // 2

    # Full-page mask (may include companion shapes for short/wide subjects)
    page_ink = _enrich_sparse_canvas(
        ink,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        ox=ox,
        oy=oy,
        seed=page_index * 997 + canvas_w,
        min_fill=0.72,
    )

    svg = build_page_svg(
        page_ink,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        offset=(0, 0),
        opttolerance=1.0,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    svg_path = out.with_suffix(".svg")
    svg_path.write_text(svg, encoding="utf-8")

    page = rasterize_svg(svg, width=canvas_w, height=canvas_h, scale=2)
    page.save(out, dpi=(dpi, dpi))
    return out


def import_art_folder(
    art_dir: Path,
    pages_dir: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.375,
) -> list[Path]:
    files = sorted(art_dir.glob("*.png")) + sorted(art_dir.glob("*.jpg"))
    if not files:
        raise FileNotFoundError(f"No images in {art_dir}")
    paths: list[Path] = []
    pages_dir.mkdir(parents=True, exist_ok=True)
    for old in pages_dir.glob("page-*"):
        if old.suffix.lower() in {".png", ".svg"}:
            old.unlink()
    for i, src in enumerate(files, start=1):
        out = pages_dir / f"page-{i:02d}.png"
        normalize_to_page(src, out, trim=trim, dpi=dpi, margin_in=margin_in, page_index=i)
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
