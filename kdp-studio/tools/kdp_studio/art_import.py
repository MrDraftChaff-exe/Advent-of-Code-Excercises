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


def _opencv_evenodd_svg(
    ink: np.ndarray,
    *,
    canvas_w: int,
    canvas_h: int,
) -> str:
    """Build page SVG from OpenCV contours (reliable even-odd holes)."""
    cnts, _ = cv2.findContours(ink.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    parts: list[str] = []
    for cnt in cnts:
        if len(cnt) < 3:
            continue
        pts = cnt.reshape(-1, 2)
        if cv2.contourArea(cnt) < 20:
            continue
        d = f"M {pts[0, 0]:.2f} {pts[0, 1]:.2f} " + " ".join(
            f"L {x:.2f} {y:.2f}" for x, y in pts[1:]
        ) + " Z"
        parts.append(d)
    d_all = " ".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" shape-rendering="geometricPrecision">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<path fill="#000000" fill-rule="evenodd" d="{d_all}"/>'
        f"</svg>\n"
    )


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
    # Ink may already be full-page (offset 0) or subject-sized
    if ox or oy:
        page = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
        h, w = ink.shape
        page[oy : oy + h, ox : ox + w] = ink
    else:
        page = ink

    curves = _trace_curves(page, opttolerance=opttolerance)
    d = " ".join(_curve_to_svg_d(c) for c in curves)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" shape-rendering="geometricPrecision">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<path fill="#000000" fill-rule="evenodd" d="{d}"/>'
        f"</svg>\n"
    )
    probe = np.array(
        rasterize_svg(svg, width=max(1, canvas_w // 4), height=max(1, canvas_h // 4), scale=1)
    )
    if float(np.mean(probe < 40)) > 0.16:
        return _opencv_evenodd_svg(page, canvas_w=canvas_w, canvas_h=canvas_h)
    return svg


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


def _ensure_colorable_strokes(ink: np.ndarray) -> np.ndarray:
    """Convert ink to explicit contour strokes safe for even-odd SVG fill.

    Silhouette fills and broken outline rings otherwise become solid black pages.
    """
    cnts, _ = cv2.findContours(ink.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(ink)
    cv2.drawContours(out, cnts, -1, 1, thickness=7)
    return out


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


def _draw_flower(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    """Daisy: round petals around a center circle."""
    petals = 6
    pr = max(16, int(r * 0.36))
    for k in range(petals):
        ang = -np.pi / 2 + k * 2 * np.pi / petals
        px = int(cx + int(r * 0.55) * np.cos(ang))
        py = int(cy + int(r * 0.55) * np.sin(ang))
        _draw_ring(page, px, py, pr, width=6)
    _draw_ring(page, cx, cy, max(14, r // 4), width=6)


def _draw_bush(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    """Rounded hedge bush with three top bumps."""
    base_y = cy + int(r * 0.55)
    bumps = [
        (cx - int(r * 0.55), cy + int(r * 0.05), int(r * 0.5)),
        (cx, cy - int(r * 0.25), int(r * 0.62)),
        (cx + int(r * 0.55), cy + int(r * 0.05), int(r * 0.5)),
    ]
    pts: list[tuple[int, int]] = [(cx - int(r * 0.95), base_y)]
    for bx, by, br in bumps:
        for ang in np.linspace(np.pi * 0.95, np.pi * 0.05, 12):
            pts.append((int(bx + br * np.cos(ang)), int(by + br * np.sin(ang))))
    pts.append((cx + int(r * 0.95), base_y))
    _draw_closed_poly(page, pts, width=6)


def _draw_leaf(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    tip = (cx, cy - r)
    left = (cx - int(r * 0.65), cy + int(r * 0.2))
    right = (cx + int(r * 0.65), cy + int(r * 0.2))
    base = (cx, cy + int(r * 0.6))
    _draw_closed_poly(page, [tip, right, base, left], width=6)
    cv2.line(page, tip, base, 1, 5, cv2.LINE_AA)


def _draw_mushroom(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    cap_r = max(24, int(r * 0.75))
    cy_cap = cy - int(r * 0.05)
    cv2.ellipse(
        page,
        (cx, cy_cap),
        (cap_r, max(18, int(cap_r * 0.65))),
        0,
        180,
        360,
        1,
        6,
        cv2.LINE_AA,
    )
    cv2.line(page, (cx - cap_r, cy_cap), (cx + cap_r, cy_cap), 1, 6, cv2.LINE_AA)
    stem_w = max(12, r // 5)
    stem_h = max(28, int(r * 0.75))
    _draw_closed_poly(
        page,
        [
            (cx - stem_w, cy_cap),
            (cx + stem_w, cy_cap),
            (cx + stem_w + 4, cy_cap + stem_h),
            (cx - stem_w - 4, cy_cap + stem_h),
        ],
        width=6,
    )


def _draw_grass_tuft(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    base = cy + int(r * 0.4)
    for dx, hscale in (
        (-int(r * 0.5), 0.8),
        (-int(r * 0.2), 1.0),
        (int(r * 0.15), 0.95),
        (int(r * 0.45), 0.75),
    ):
        tip = (cx + dx, cy - int(r * hscale))
        cv2.line(page, (cx, base), tip, 1, 6, cv2.LINE_AA)
    cv2.line(page, (cx - r, base), (cx + r, base), 1, 5, cv2.LINE_AA)


def _draw_simple_star(page: np.ndarray, cx: int, cy: int, r: int) -> None:
    pts = []
    for k in range(10):
        ang = -np.pi / 2 + k * np.pi / 5
        rr = r if k % 2 == 0 else max(10, int(r * 0.4))
        pts.append((int(cx + rr * np.cos(ang)), int(cy + rr * np.sin(ang))))
    _draw_closed_poly(page, pts, width=6)


def _draw_motif(page: np.ndarray, cx: int, cy: int, r: int, kind: int, *, theme: str = "forest") -> None:
    """Theme-appropriate companions — never generic nuts-and-bolts geometry for nature books."""
    t = (theme or "forest").lower()
    if "forest" in t or "animal" in t or "quiet" in t or "cozy" in t:
        # Prefer flowers & bushes; occasional leaf / mushroom / grass
        pick = kind % 10
        if pick <= 3:
            _draw_flower(page, cx, cy, r)
        elif pick <= 6:
            _draw_bush(page, cx, cy, r)
        elif pick <= 7:
            _draw_leaf(page, cx, cy, r)
        elif pick <= 8:
            _draw_mushroom(page, cx, cy, r)
        else:
            _draw_grass_tuft(page, cx, cy, r)
        return
    if "sea" in t or "ocean" in t:
        if kind % 3 == 0:
            _draw_ring(page, cx, cy, r, width=6)
            _draw_ring(page, cx, cy, max(12, r // 3), width=5)
        elif kind % 3 == 1:
            # seashell swirl (nested arcs as closed petal)
            _draw_flower(page, cx, cy, r)
        else:
            _draw_leaf(page, cx, cy, r)  # seaweed-ish
        return
    if "space" in t:
        if kind % 2 == 0:
            _draw_simple_star(page, cx, cy, r)
        else:
            _draw_ring(page, cx, cy, r, width=6)
            _draw_ring(page, cx, cy, max(10, r // 4), width=5)
        return
    if "sport" in t:
        _draw_ring(page, cx, cy, r, width=7)
        _draw_ring(page, cx, cy, max(12, r // 3), width=6)
        return
    # Math / science / chemistry: soft organic dots & petals, not hex bolts
    if kind % 2 == 0:
        _draw_flower(page, cx, cy, r)
    else:
        _draw_ring(page, cx, cy, r, width=6)
        _draw_ring(page, cx, cy, max(10, r // 4), width=5)


def _fill_band_with_motifs(
    page: np.ndarray,
    *,
    bx0: int,
    by0: int,
    bx1: int,
    by1: int,
    rng: np.random.Generator,
    theme: str = "forest",
) -> None:
    """Pack medium/large closed shapes into an empty rectangle."""
    bw, bh = bx1 - bx0, by1 - by0
    if bw < 100 or bh < 90:
        return
    t = (theme or "").lower()
    foresty = "forest" in t or "animal" in t
    # Forest pages: fewer, larger bushes/flowers so they read as scenery
    if foresty:
        r_hi = max(70, min(160, int(bh * 0.48), int(bw * 0.18)))
        r_lo = max(55, int(r_hi * 0.72))
        cols = max(2, min(3, bw // max(200, r_hi * 2 + 50)))
        rows = max(1, min(2, bh // max(160, r_hi * 2 + 40)))
    else:
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
            _draw_motif(page, cx, cy, r, int(rng.integers(0, 5)), theme=theme)


def _enrich_sparse_canvas(
    ink: np.ndarray,
    *,
    canvas_w: int,
    canvas_h: int,
    ox: int,
    oy: int,
    seed: int,
    min_fill: float = 0.72,
    theme: str = "forest",
) -> np.ndarray:
    """If the subject leaves large empty bands, add themed companions to color.

    Companion motifs only — never a page-sized frame (those become solid black
    under even-odd vector fill). Returns a full-page ink mask (1=ink).
    """
    page = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    h, w = ink.shape
    page[oy : oy + h, ox : ox + w] = ink

    # Bold-and-easy STYLE.md titles — never sprinkle companion junk
    t = (theme or "").lower()
    if any(
        k in t
        for k in (
            "quiet",
            "cozy",
            "stained",
            "cars",
            "planes",
            "buildings",
            "food",
            "mountains",
            "fantasy",
            "dress",
            "cryptid",
            "yokai",
            "construction",
        )
    ):
        return page

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
        _fill_band_with_motifs(page, bx0=bx0, by0=by0, bx1=bx1, by1=by1, rng=rng, theme=theme)

    return page


def prepare_line_art(gray: Image.Image) -> Image.Image:
    """Fallback raster-only helper (prefer normalize_to_page for SVG+PNG)."""
    ink = _build_ink_mask(gray)
    h, w = ink.shape
    svg = build_page_svg(ink, canvas_w=w, canvas_h=h, offset=(0, 0))
    return rasterize_svg(svg, width=w, height=h, scale=2)


def _normalize_quiet_raster(
    src: Path,
    out: Path,
    *,
    trim: str = "square",
    dpi: int = 300,
    margin_in: float = 0.375,
) -> Path:
    """Place STYLE.md ink art on the page without re-binarizing.

    Soft anti-aliased ink must be resized with LANCZOS and pasted as grayscale.
    Re-thresholding after resize is what created torn/broken strokes.
    """
    width_in, height_in = trim_box(trim)
    canvas_w = int(round(width_in * dpi))
    canvas_h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    inner = (canvas_w - 2 * margin, canvas_h - 2 * margin)

    im = Image.open(src).convert("RGB")
    im = _crop_to_ink(im, threshold=230)
    fitted = ImageOps.contain(im, inner, Image.Resampling.LANCZOS)

    page = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    ox = (canvas_w - fitted.size[0]) // 2
    oy = (canvas_h - fitted.size[1]) // 2
    page.paste(fitted, (ox, oy))

    # Limit soft-AA gray levels after LANCZOS so PDFs stay compressible
    # while edges remain continuous (not hard-binarized).
    arr = np.asarray(page.convert("L"), dtype=np.float32)
    aa_steps = 12
    step = 255.0 / aa_steps
    arr = np.clip(np.round(arr / step) * step, 0, 255).astype(np.uint8)
    page = Image.fromarray(arr, mode="L").convert("RGB")

    out.parent.mkdir(parents=True, exist_ok=True)
    page.save(out, dpi=(dpi, dpi), optimize=True, compress_level=9)
    svg_path = out.with_suffix(".svg")
    if svg_path.exists():
        svg_path.unlink()
    return out


def normalize_to_page(
    src: Path,
    out: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.375,
    page_index: int = 1,
    theme: str = "forest",
) -> Path:
    """Place art large on the page; add themed companions if still sparse."""
    t = (theme or "").lower()
    if any(
        k in t
        for k in (
            "quiet",
            "cozy",
            "stained",
            "cars",
            "planes",
            "buildings",
            "food",
            "mountains",
            "fantasy",
            "dress",
            "cryptid",
            "yokai",
            "construction",
        )
    ):
        return _normalize_quiet_raster(src, out, trim=trim, dpi=dpi, margin_in=margin_in)

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
        theme=theme,
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
    theme: str = "forest",
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
        normalize_to_page(
            src, out, trim=trim, dpi=dpi, margin_in=margin_in, page_index=i, theme=theme
        )
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
