"""Normalize external/AI line-art into KDP page PNGs with gap closing."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .specs import trim_box


def _skeletonize(ink: np.ndarray) -> np.ndarray:
    """Morphological skeleton of binary ink (1=ink)."""
    img = ink.astype(np.uint8).copy()
    skel = np.zeros_like(img)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while True:
        opened = cv2.morphologyEx(img, cv2.MORPH_OPEN, element)
        temp = cv2.subtract(img, opened)
        eroded = cv2.erode(img, element)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded
        if cv2.countNonZero(img) == 0:
            break
    return skel


def _skeleton_endpoints(skel: np.ndarray) -> list[tuple[int, int]]:
    """(x, y) skeleton pixels with exactly one 8-neighbor."""
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
    neighbors = cv2.filter2D(skel, -1, kernel)
    ys, xs = np.where((skel > 0) & (neighbors == 1))
    return list(zip(xs.tolist(), ys.tolist()))


def _snap_skeleton_ends(ink: np.ndarray, *, max_dist: int = 32) -> np.ndarray:
    """Join skeleton stroke ends across white gaps to nearest foreign ink."""
    skel = _skeletonize(ink)
    ends = _skeleton_endpoints(skel)
    if not ends:
        return ink

    # Cap for speed — prefer ends spread across the image
    if len(ends) > 900:
        step = max(1, len(ends) // 900)
        ends = ends[::step]

    h, w = ink.shape
    out = ink.copy()
    max_d2 = max_dist * max_dist
    for x, y in ends:
        y0, y1 = max(0, y - max_dist), min(h, y + max_dist + 1)
        x0, x1 = max(0, x - max_dist), min(w, x + max_dist + 1)
        roi = ink[y0:y1, x0:x1]
        yy, xx = np.ogrid[y0:y1, x0:x1]
        dist2 = (xx - x) ** 2 + (yy - y) ** 2
        # Foreign ink: outside the local stroke nub
        mask = (roi > 0) & (dist2 > 25) & (dist2 <= max_d2)
        if not np.any(mask):
            continue
        # Also require that the straight path crosses some white (a real gap)
        candidates = np.argwhere(mask)
        best = None
        best_d = max_d2 + 1
        for cy, cx in candidates:
            tx, ty = x0 + int(cx), y0 + int(cy)
            d = int(dist2[cy, cx])
            if d >= best_d:
                continue
            # Sample midpoint — must be white on original to count as a tear
            mx, my = (x + tx) // 2, (y + ty) // 2
            if ink[my, mx] == 0:
                best = (tx, ty)
                best_d = d
        if best is not None:
            cv2.line(out, (x, y), best, 1, thickness=5, lineType=cv2.LINE_8)
    return out


def _bridge_nearby_ends(ink: np.ndarray, *, max_dist: int = 40) -> np.ndarray:
    """Connect pairs of skeleton ends that face each other across a gap."""
    skel = _skeletonize(ink)
    ends = _skeleton_endpoints(skel)
    if len(ends) < 2:
        return ink
    if len(ends) > 700:
        ends = ends[:: max(1, len(ends) // 700)]

    pts = np.array(ends, dtype=np.float32)
    out = ink.copy()
    used: set[int] = set()
    max_d2 = float(max_dist * max_dist)
    for i, p in enumerate(pts):
        if i in used:
            continue
        best_j, best_d2 = -1, max_d2
        for j in range(i + 1, len(pts)):
            if j in used:
                continue
            d2 = float((p[0] - pts[j][0]) ** 2 + (p[1] - pts[j][1]) ** 2)
            if 16.0 < d2 < best_d2:
                mx, my = int((p[0] + pts[j][0]) / 2), int((p[1] + pts[j][1]) / 2)
                if 0 <= my < ink.shape[0] and 0 <= mx < ink.shape[1] and ink[my, mx] == 0:
                    best_d2 = d2
                    best_j = j
        if best_j >= 0:
            used.add(i)
            used.add(best_j)
            a = (int(pts[i][0]), int(pts[i][1]))
            b = (int(pts[best_j][0]), int(pts[best_j][1]))
            cv2.line(out, a, b, 1, thickness=5, lineType=cv2.LINE_8)
    return out


def _fill_stroke_pinholes(ink: np.ndarray, *, max_hole: int = 40) -> np.ndarray:
    """Fill tiny white holes inside black strokes (pixel tears in thick lines)."""
    # White components that don't touch the border and are small
    white = (1 - ink).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=8)
    out = ink.copy()
    h, w = ink.shape
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area > max_hole:
            continue
        # Skip if component touches image border (true background)
        comp = labels[y : y + bh, x : x + bw] == i
        # Check global border touch via bbox
        if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
            # might still be interior — check properly
            ys, xs = np.where(labels == i)
            if ys.min() == 0 or xs.min() == 0 or ys.max() == h - 1 or xs.max() == w - 1:
                continue
        out[labels == i] = 1
    return out


def _seal_thin_cracks(ink: np.ndarray, *, length: int = 11) -> np.ndarray:
    """Close hairline cracks with short horizontal/vertical structuring elements.

    Seals tears that cut through thick strokes without filling large color areas.
    """
    length = max(3, length | 1)
    kh = cv2.getStructuringElement(cv2.MORPH_RECT, (length, 1))
    kv = cv2.getStructuringElement(cv2.MORPH_RECT, (1, length))
    out = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, kh, iterations=1)
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, kv, iterations=1)
    # Mild diagonal help via small ellipse
    ke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (length, length))
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, ke, iterations=1)
    return out


def _seal_narrow_corridors(ink: np.ndarray, *, max_gap: int = 8) -> np.ndarray:
    """Fill white pixels that sit in a narrow corridor between ink on opposite sides."""
    # Distance to nearest ink
    dist = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 3)
    # Candidate corridor pixels: close to ink (<= max_gap/2 roughly) but white
    cand = (ink == 0) & (dist > 0) & (dist <= (max_gap / 2.0 + 0.5))
    if not np.any(cand):
        return ink

    # For speed, only inspect candidates
    ys, xs = np.where(cand)
    h, w = ink.shape
    out = ink.copy()
    for y, x in zip(ys.tolist(), xs.tolist()):
        # Horizontal narrowness
        dl = next((d for d in range(1, max_gap + 1) if x - d >= 0 and ink[y, x - d]), None)
        dr = next((d for d in range(1, max_gap + 1) if x + d < w and ink[y, x + d]), None)
        if dl is not None and dr is not None and dl + dr <= max_gap:
            out[y, x] = 1
            continue
        du = next((d for d in range(1, max_gap + 1) if y - d >= 0 and ink[y - d, x]), None)
        dd = next((d for d in range(1, max_gap + 1) if y + d < h and ink[y + d, x]), None)
        if du is not None and dd is not None and du + dd <= max_gap:
            out[y, x] = 1
    return out


def _fill_notches(ink: np.ndarray, *, min_neighbors: int = 5, passes: int = 2) -> np.ndarray:
    """Paint white pixels black when mostly surrounded by ink (notches/tears)."""
    kernel = np.ones((3, 3), dtype=np.uint8)
    out = ink.copy()
    for _ in range(passes):
        neighbor_sum = cv2.filter2D(out, -1, kernel)
        # neighbor_sum includes center; subtract center contribution
        surrounded = (out == 0) & ((neighbor_sum - out) >= min_neighbors)
        if not np.any(surrounded):
            break
        out[surrounded] = 1
    return out


def close_line_gaps(
    gray: Image.Image,
    *,
    close_px: int = 17,
    use_skeleton: bool = True,
) -> Image.Image:
    """Bridge broken outlines and seal micro-tears in black line art."""
    arr = np.array(gray.convert("L"))
    ink = (arr < 200).astype(np.uint8)

    # Strong morphological close first (bridges most AI outline gaps)
    size = max(3, close_px | 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k, iterations=3)

    if use_skeleton:
        # Skeleton-aware bridging for residual tears (eyes, junctions, fur tips)
        closed = _bridge_nearby_ends(closed, max_dist=max(36, close_px * 2))
        closed = _snap_skeleton_ends(closed, max_dist=max(28, close_px + 10))
        closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, k, iterations=2)

    # Seal hairline cracks through thick strokes (common near eyes)
    closed = _seal_thin_cracks(closed, length=max(9, close_px // 2 | 1))
    closed = _seal_narrow_corridors(closed, max_gap=8)

    # Fill pinholes inside strokes
    closed = _fill_stroke_pinholes(closed, max_hole=120)
    closed = _fill_notches(closed, min_neighbors=5, passes=3)

    # Thicken for marker-friendly print lines
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    closed = cv2.dilate(closed, k2, iterations=1)
    # Small close after thicken seals notches at junctions (eyes/mask)
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, k3, iterations=1)
    closed = _seal_thin_cracks(closed, length=11)
    closed = _fill_stroke_pinholes(closed, max_hole=80)
    closed = _fill_notches(closed, min_neighbors=4, passes=2)

    # Final junction merge — closes remaining eye/mask micro-gaps
    k4 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.dilate(closed, k4, iterations=1)
    closed = _fill_notches(closed, min_neighbors=4, passes=3)
    closed = _seal_thin_cracks(closed, length=13)
    closed = _fill_stroke_pinholes(closed, max_hole=100)

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
    g0 = ImageOps.grayscale(im)
    bw0 = g0.point(lambda p: 0 if p < 190 else 255)
    # Full seal at source resolution (cheaper + gaps are fewer px)
    bw0 = close_line_gaps(bw0, close_px=17, use_skeleton=True)

    fitted = ImageOps.contain(bw0.convert("RGB"), inner, Image.Resampling.NEAREST)
    g = fitted.convert("L")
    bw = g.point(lambda p: 0 if p < 190 else 255)
    # Page scale: morph + pinhole only (skeletonize on 2550px pages is too slow)
    bw = close_line_gaps(bw, close_px=23, use_skeleton=False)

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
    for old in pages_dir.glob("page-*.png"):
        old.unlink()
    for i, src in enumerate(files, start=1):
        out = pages_dir / f"page-{i:02d}.png"
        normalize_to_page(src, out, trim=trim, dpi=dpi, margin_in=margin_in)
        paths.append(out)
    return paths
