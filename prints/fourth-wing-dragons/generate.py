#!/usr/bin/env python3
"""Tairn, Sgaeyl, and Andarna for the Flashforge AD5X.

Three dragons share one red perch. Each dragon is its own PLA filament,
and the perch is the fourth channel. The loaded colors are white, black,
red, and blue.

  1  black   Tairn, large, morningstar tail
  2  blue    Sgaeyl, dagger tail
  3  white   Andarna, small, feather tail
  4  red     the perch

The pose is a low crouch. Bellies, feet, wing elbows, and tails sit in the
perch so the print does not need support.

Run:
  python3 generate.py --quality preview
  python3 generate.py --quality final
"""

from __future__ import annotations

import argparse
import json
import struct
import zipfile
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh
from numba import njit
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
PREVIEW = HERE / "preview"

# Local z = 0 is the top of the perch. Negative z is buried in the stone.
BASE_TOP = 10.0

PALETTE = [
    {
        "slot": 1,
        "key": "tairn",
        "name": "Tairn",
        "detail": "large black dragon, morningstar tail",
        "hex": "#161616",
        "material": "PLA",
    },
    {
        "slot": 2,
        "key": "sgaeyl",
        "name": "Sgaeyl",
        "detail": "blue dragon, dagger tail",
        "hex": "#1E4FFF",
        "material": "PLA",
    },
    {
        "slot": 3,
        "key": "andarna",
        "name": "Andarna",
        "detail": "small white dragon, feather tail",
        "hex": "#F4F4F4",
        "material": "PLA",
    },
    {
        "slot": 4,
        "key": "perch",
        "name": "Red perch",
        "detail": "shared base",
        "hex": "#E10600",
        "material": "PLA",
    },
]


def set_quality(name: str) -> None:
    if name == "preview":
        mf.set_min_circular_angle(8.0)
        mf.set_min_circular_edge_length(0.55)
    elif name == "final":
        # 4 degrees keeps horns, snouts, and the perch round instead of faceted.
        mf.set_min_circular_angle(4.0)
        mf.set_min_circular_edge_length(0.30)
    else:
        raise SystemExit(f"unknown quality {name}")
    mf.set_circular_segments(0)


def ell(center, radii) -> mf.Manifold:
    rx, ry, rz = radii
    big = max(rx, ry, rz)
    return (
        mf.Manifold.sphere(big)
        .scale((rx / big, ry / big, rz / big))
        .translate(tuple(center))
    )


def ball(center, radius) -> mf.Manifold:
    return mf.Manifold.sphere(radius).translate(tuple(center))


def link(a, ra, b, rb) -> mf.Manifold:
    return mf.Manifold.batch_hull([ball(a, ra), ball(b, rb)])


def union_all(parts: list[mf.Manifold]) -> mf.Manifold:
    parts = [p for p in parts if p is not None and not p.is_empty()]
    if not parts:
        return mf.Manifold()
    if len(parts) == 1:
        return parts[0]
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)


def both(solid: mf.Manifold) -> mf.Manifold:
    return solid + solid.mirror((1.0, 0.0, 0.0))


def z_range(solid: mf.Manifold, z0: float, z1: float) -> mf.Manifold:
    return solid.trim_by_plane((0.0, 0.0, 1.0), z0).trim_by_plane(
        (0.0, 0.0, -1.0), -z1
    )


def drop_dust(solid: mf.Manifold, min_volume: float = 30.0) -> mf.Manifold:
    if solid.is_empty():
        return solid
    kept = [p for p in solid.decompose() if p.volume() >= min_volume]
    return union_all(kept)


def require_ok(solid: mf.Manifold, label: str) -> None:
    status = str(solid.status())
    if "NoError" not in status:
        raise RuntimeError(f"{label} boolean status {status}")


def P(s: float, x: float, y: float, z: float):
    return (x * s, y * s, z * s)


def R(s: float, radius: float, floor: float = 0.0) -> float:
    return max(floor, radius * s)


# ---------------------------------------------------------------------------
# Dragons
# ---------------------------------------------------------------------------

def build_dragon(scale: float, kind: str, slender: float = 1.0) -> mf.Manifold:
    """Low crouch. z = 0 is the perch top; anything below that is buried."""
    s = scale
    parts: list[mf.Manifold] = []

    body = ell(
        P(s, 0.0, -2.0, 4.2),
        (R(s, 13.0 / slender), R(s, 22.0 * slender), R(s, 12.0)),
    )
    parts.append(body)

    # Neck and snout are a chain of spheres so the profile stays round, then
    # a chin hull fills the cusps under them. Bare sphere bottoms print as ledges.
    for x, y, z, radius in (
        (0.0, 10.0, 7.2, 7.6),
        (0.0, 20.0, 10.4, 6.8),
        (0.0, 30.0, 12.2, 6.2),
        (0.0, 38.0, 12.4, 5.4),
        (0.0, 46.0, 11.0, 4.2),
        (0.0, 52.0, 10.2, 3.0),
    ):
        parts.append(ball(P(s, x, y, z), R(s, radius)))
    parts.append(
        mf.Manifold.batch_hull(
            [
                ball(P(s, 0.0, 10.0, 6.0), R(s, 7.4)),
                ball(P(s, 0.0, 28.0, 8.0), R(s, 6.0)),
                ball(P(s, 0.0, 42.0, 2.0), R(s, 5.8)),
                ball(P(s, 0.0, 50.0, 4.0), R(s, 3.6)),
            ]
        )
    )

    for side in (-1.0, 1.0):
        parts.append(
            link(
                P(s, side * 2.4, 32.0, 14.5),
                R(s, 2.2, 1.8),
                P(s, side * 3.6, 23.0, 27.0),
                R(s, 1.15, 1.35),
            )
        )

    for y in (-14.0, -6.0, 2.0, 10.0):
        parts.append(
            link(
                P(s, 0.0, y, 11.5),
                R(s, 2.1, 1.6),
                P(s, 0.0, y - 1.2, 19.5),
                R(s, 0.95, 1.25),
            )
        )

    for side in (-1.0, 1.0):
        # Folded wing: shoulder in the ribs, wrist raised, elbow and tip on the stone.
        shoulder = (P(s, side * 5.5, 8.0, 9.5), R(s, 4.4))
        wrist = (P(s, side * 8.2, 1.5, 17.2), R(s, 2.9, 2.0))
        elbow = (P(s, side * 14.5, -5.0, 0.0), R(s, 3.3, 2.4))
        tip = (P(s, side * 11.0, -18.0, 0.0), R(s, 2.6, 2.0))
        trail = (P(s, side * 6.0, -14.0, 0.0), R(s, 2.7, 2.0))
        parts.append(link(*shoulder, *wrist))
        parts.append(link(*wrist, *elbow))
        parts.append(link(*elbow, *tip))
        parts.append(link(*tip, *trail))
        parts.append(
            link(
                P(s, side * 8.2, 1.5, 16.4),
                R(s, 2.0, 1.6),
                P(s, side * 10.2, -0.5, 24.5),
                R(s, 1.1, 1.3),
            )
        )

    feet = (
        (8.0, 12.0, 5.0, 8.4, 16.0),
        (-8.0, 12.0, 5.0, -8.4, 16.0),
        (8.5, -12.0, 4.0, 9.2, -16.0),
        (-8.5, -12.0, 4.0, -9.2, -16.0),
    )
    for hx, hy, hz, fx, fy in feet:
        parts.append(
            link(
                P(s, hx, hy, hz),
                R(s, 4.5),
                P(s, fx, fy, -0.6),
                R(s, 3.8, 2.6),
            )
        )

    if kind == "morningstar":
        parts.extend(_morningstar_tail(s))
    elif kind == "dagger":
        parts.extend(_dagger_tail(s))
    elif kind == "feather":
        parts.extend(_feather_tail(s))
    else:
        raise SystemExit(f"unknown dragon kind {kind}")

    solid = union_all(parts)
    solid = _carve_face(solid, s)
    require_ok(solid, kind)
    return drop_dust(solid)


def _chain(points: list[tuple]) -> list[mf.Manifold]:
    balls = [ball(p, r) for p, r in points]
    links = [mf.Manifold.batch_hull([a, b]) for a, b in zip(balls, balls[1:])]
    return links


def _morningstar_tail(s: float) -> list[mf.Manifold]:
    rump = R(s, 6.2)
    points = [
        (P(s, 0.0, -20.0, 0.2), rump),
        (P(s, 12.0, -32.0, 0.0), R(s, 5.0, 2.4)),
        (P(s, 26.0, -34.0, 0.0), R(s, 4.4, 2.2)),
        (P(s, 36.0, -22.0, 1.4), R(s, 8.2)),
    ]
    parts = _chain(points)
    center = np.array(points[-1][0], dtype=float)
    radius = points[-1][1]
    directions = (
        (0.0, 0.05, 1.0),
        (0.38, 0.22, 1.0),
        (-0.34, 0.28, 1.0),
        (0.42, -0.18, 1.0),
        (-0.16, -0.42, 1.0),
        (0.12, 0.48, 1.0),
    )
    for raw in directions:
        direction = np.array(raw, dtype=float)
        direction /= np.linalg.norm(direction)
        base = center + direction * (radius * 0.45)
        tip = center + direction * (radius + R(s, 6.5, 5.0))
        parts.append(link(tuple(base), R(s, 2.3, 1.8), tuple(tip), R(s, 1.15, 1.25)))
    return parts


def _dagger_tail(s: float) -> list[mf.Manifold]:
    points = [
        (P(s, 0.0, -20.0, 0.2), R(s, 5.4)),
        (P(s, 2.0, -32.0, 0.0), R(s, 4.2, 2.2)),
        (P(s, 0.0, -40.0, 0.0), R(s, 3.2, 2.0)),
    ]
    parts = _chain(points)
    blade = mf.Manifold.batch_hull(
        [
            ball(P(s, 0.0, -38.0, 0.0), R(s, 3.4, 2.2)),
            ball(P(s, 0.0, -56.0, 0.3), R(s, 1.5, 1.6)),
            ball(P(s, 5.0, -46.0, 0.0), R(s, 1.5, 1.6)),
            ball(P(s, -5.0, -46.0, 0.0), R(s, 1.5, 1.6)),
        ]
    )
    parts.append(blade)
    return parts


def _feather_tail(s: float) -> list[mf.Manifold]:
    parts = _chain(
        [
            (P(s, 0.0, -16.0, 0.2), R(s, 4.6, 2.2)),
            (P(s, 0.0, -24.0, 0.0), R(s, 3.2, 2.0)),
        ]
    )
    length = max(11.0, 16.0 * s)
    width = max(2.4, 3.6 * s)
    thick = max(2.2, 2.6 * s)
    for ang in (-58.0, -30.0, 0.0, 30.0, 58.0):
        feather = ell((0.0, 0.0, 0.0), (width, length, thick))
        feather = feather.translate((0.0, -length * 0.85, 0.0))
        feather = feather.rotate((0.0, 0.0, ang))
        feather = feather.translate(P(s, 0.0, -18.0, 0.0))
        parts.append(feather)
    return parts


def _carve_face(solid: mf.Manifold, s: float) -> mf.Manifold:
    eye = ell(P(s, 4.8, 38.0, 13.4), (R(s, 2.1, 1.4), R(s, 2.4, 1.5), R(s, 1.8, 1.3)))
    nostril = ball(P(s, 1.5, 51.5, 10.6), R(s, 1.05, 0.9))
    carved = solid - both(eye) - both(nostril)
    require_ok(carved, "face")
    return carved


def place(solid: mf.Manifold, x: float, y: float, yaw: float) -> mf.Manifold:
    return solid.rotate((0.0, 0.0, yaw)).translate((x, y, BASE_TOP))


def build_perch() -> mf.Manifold:
    # Rocks stay inside the oval. A sphere that hangs past the rim leaves
    # an unsupported belly where the slab no longer sits underneath it.
    slab = mf.Manifold.cylinder(BASE_TOP, 86.0, 86.0, 96).scale((1.0, 0.84, 1.0))
    mask = mf.Manifold.cylinder(BASE_TOP + 18.0, 86.0, 86.0, 96).scale((1.0, 0.84, 1.0))
    specs = (
        (-70.0, -42.0, 6.4),
        (64.0, -44.0, 6.8),
        (72.0, 6.0, 5.8),
        (-74.0, 16.0, 6.2),
        (6.0, 50.0, 5.6),
        (-18.0, -52.0, 6.0),
        (50.0, 40.0, 5.4),
        (-56.0, 42.0, 5.8),
        (36.0, -50.0, 5.2),
    )
    rocks = [ball((x, y, BASE_TOP - 0.2), radius) for x, y, radius in specs]
    return union_all([slab, union_all(rocks) ^ mask])


def build_scene() -> dict:
    tairn = place(build_dragon(1.02, "morningstar", slender=0.96), -2.0, -4.0, 10.0)
    sgaeyl = place(build_dragon(0.80, "dagger", slender=1.14), -58.0, 2.0, -16.0)
    andarna = place(build_dragon(0.50, "feather", slender=1.05), 46.0, 28.0, 18.0)
    return {
        "tairn": tairn,
        "sgaeyl": sgaeyl,
        "andarna": andarna,
        "perch_src": build_perch(),
    }


def cut_overlap(solid: mf.Manifold, cutter: mf.Manifold) -> mf.Manifold:
    """Subtract only when the solids actually share volume.

    A boolean along a merely touching face stacks vertices, and a slicer
    weld turns that into a non-manifold edge.
    """
    if solid.is_empty() or cutter.is_empty():
        return solid
    shared = solid ^ cutter
    if shared.is_empty() or shared.volume() < 1.0:
        return solid
    return drop_dust(solid - cutter)


def assign_colors(raw: dict) -> dict[str, mf.Manifold]:
    tairn = drop_dust(raw["tairn"])
    sgaeyl = drop_dust(cut_overlap(raw["sgaeyl"], tairn))
    andarna = drop_dust(cut_overlap(cut_overlap(raw["andarna"], tairn), sgaeyl))
    perch = drop_dust(raw["perch_src"] - tairn - sgaeyl - andarna)
    parts = {
        "tairn": tairn,
        "sgaeyl": sgaeyl,
        "andarna": andarna,
        "perch": perch,
    }
    for key, solid in parts.items():
        require_ok(solid, key)
        if solid.is_empty():
            raise RuntimeError(f"{key} mesh is empty")
    return parts


def settle_on_bed(parts: dict[str, mf.Manifold]) -> dict[str, mf.Manifold]:
    boxes = [p.bounding_box() for p in parts.values()]
    zmin = min(b[2] for b in boxes)
    xmin = min(b[0] for b in boxes)
    xmax = max(b[3] for b in boxes)
    ymin = min(b[1] for b in boxes)
    ymax = max(b[4] for b in boxes)
    dx = -0.5 * (xmin + xmax)
    dy = -0.5 * (ymin + ymax)
    dz = -zmin
    shift = (dx, dy, dz)
    return {k: v.translate(shift) for k, v in parts.items()}


# ---------------------------------------------------------------------------
# Mesh conversion, checks, previews
# ---------------------------------------------------------------------------

def to_trimesh(solid: mf.Manifold) -> trimesh.Trimesh:
    mesh = solid.to_mesh()
    verts = np.asarray(mesh.vert_properties[:, :3], dtype=np.float64)
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    tri = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    tri.merge_vertices(digits_vertex=5)
    tri.update_faces(tri.nondegenerate_faces())
    tri.remove_unreferenced_vertices()
    return tri


def assert_export_mesh(mesh: trimesh.Trimesh, label: str) -> None:
    """A slicer welds vertices. The welded shell has to be closed."""
    if not mesh.is_watertight or mesh.volume <= 1.0:
        raise RuntimeError(
            f"{label} is not a closed mesh (watertight={mesh.is_watertight}, volume={mesh.volume:.1f})"
        )


def hex_to_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def _raster_polygons(polys, origin, pitch, nx, ny) -> np.ndarray:
    """Even-odd fill of slice contours. Row is Y, column is X."""
    acc = np.zeros((ny, nx), dtype=bool)
    ox, oy = float(origin[0]), float(origin[1])
    for poly in polys:
        if len(poly) < 3:
            continue
        im = Image.new("1", (nx, ny), 0)
        draw = ImageDraw.Draw(im)
        pts = [((float(p[0]) - ox) / pitch, (float(p[1]) - oy) / pitch) for p in poly]
        draw.polygon(pts, fill=1)
        acc ^= np.asarray(im, dtype=bool)
    return acc


def voxel_report(parts: dict[str, mf.Manifold], pitch: float = 0.85):
    """Solid cross-section voxels for support, balance, and orthographic previews."""
    boxes = [p.bounding_box() for p in parts.values()]
    vmin = np.array([min(b[i] for b in boxes) for i in range(3)], dtype=np.float64) - pitch
    vmax = np.array([max(b[i + 3] for b in boxes) for i in range(3)], dtype=np.float64) + pitch
    dims = np.maximum(np.ceil((vmax - vmin) / pitch).astype(int), 1)
    volume = np.zeros((*dims, 4), dtype=np.float32)
    zs = vmin[2] + (np.arange(dims[2]) + 0.5) * pitch

    order = ["perch", "andarna", "sgaeyl", "tairn"]
    for key in order:
        color = hex_to_rgb(next(p["hex"] for p in PALETTE if p["key"] == key))
        solid = parts[key]
        for zi, z in enumerate(zs):
            cs = solid.slice(float(z))
            if cs.is_empty():
                continue
            mask = _raster_polygons(cs.to_polygons(), vmin[:2], pitch, int(dims[0]), int(dims[1]))
            ys, xs = np.nonzero(mask)
            if len(xs) == 0:
                continue
            volume[xs, ys, zi, :3] = color
            volume[xs, ys, zi, 3] = 1.0

    occ = volume[..., 3] > 0.5
    # 3x3 neighborhood on the layer below allows a 45 degree slope.
    below = np.zeros_like(occ)
    below[:, :, 1:] = occ[:, :, :-1]
    support = below.copy()
    support[1:, :, 1:] |= occ[:-1, :, :-1]
    support[:-1, :, 1:] |= occ[1:, :, :-1]
    support[:, 1:, 1:] |= occ[:, :-1, :-1]
    support[:, :-1, 1:] |= occ[:, 1:, :-1]
    support[1:, 1:, 1:] |= occ[:-1, :-1, :-1]
    support[1:, :-1, 1:] |= occ[:-1, 1:, :-1]
    support[:-1, 1:, 1:] |= occ[1:, :-1, :-1]
    support[:-1, :-1, 1:] |= occ[1:, 1:, :-1]
    bad = occ.copy()
    world_z = vmin[2] + (np.arange(occ.shape[2]) + 0.5) * pitch
    bad[:, :, world_z <= pitch * 1.35] = False
    bad[:, :, 1:] &= ~support[:, :, 1:]
    bad_idx = np.argwhere(bad)

    # Stability: center of mass over the convex hull of the sole.
    idx = np.argwhere(occ)
    centers = vmin + (idx + 0.5) * pitch
    com = centers.mean(axis=0)
    sole = centers[centers[:, 2] <= vmin[2] + pitch * 2.2]
    hull = ConvexHull(sole[:, :2])
    eq = hull.equations
    margin = float(np.min(-(eq[:, :2] @ com[:2] + eq[:, 2])))

    return {
        "volume": volume,
        "vmin": vmin,
        "pitch": pitch,
        "unsupported": bad_idx,
        "com": com,
        "sole_margin_mm": margin,
        "origin_z": float(vmin[2]),
    }


def _project(volume, axis: int, which: str) -> np.ndarray:
    alpha = volume[..., 3]
    rank = np.where(alpha > 0.5, alpha, -1.0)
    if which == "max":
        pick = rank.argmax(axis=axis)
    else:
        # min index among occupied; invert by argmax of reversed rank
        rev = np.where(alpha > 0.5, -alpha, -1.0)
        # smaller index wins if we scan from 0: use where + max of (large - index)
        n = alpha.shape[axis]
        shape = [1, 1, 1]
        shape[axis] = n
        index = np.arange(n).reshape(shape)
        score = np.where(alpha > 0.5, (n - index).astype(np.float32), -1.0)
        pick = score.argmax(axis=axis)
    any_occ = (alpha > 0.5).any(axis=axis)
    # Gather
    if axis == 0:
        ys = np.arange(pick.shape[0])[:, None]
        zs = np.arange(pick.shape[1])[None, :]
        cols = volume[pick, ys, zs]
    elif axis == 1:
        xs = np.arange(pick.shape[0])[:, None]
        zs = np.arange(pick.shape[1])[None, :]
        cols = volume[xs, pick, zs]
    else:
        xs = np.arange(pick.shape[0])[:, None]
        ys = np.arange(pick.shape[1])[None, :]
        cols = volume[xs, ys, pick]
    cols = cols.copy()
    # any_occ broadcasts against the gathered plane
    cols[~any_occ] = 0
    return cols


def save_voxel_views(report, path: Path) -> None:
    volume = report["volume"]
    # front: looking along -Y, so the max-Y occupied voxel is in front
    front = _project(volume, 1, "max")  # (nx, nz, 4)
    side = _project(volume, 0, "max")  # right side, (ny, nz, 4)
    back = _project(volume, 1, "min")
    views = {"front": front, "side": side, "back": back}
    path.mkdir(parents=True, exist_ok=True)
    for name, cols in views.items():
        rgb = cols[:, ::-1, :3]  # z up
        rgb = np.transpose(rgb, (1, 0, 2))
        img = np.full((*rgb.shape[:2], 3), 0.94, dtype=np.float32)
        mask = cols[:, ::-1, 3] > 0.5
        mask = np.transpose(mask)
        img[mask] = rgb[mask]
        scale = 4
        big = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
        Image.fromarray((np.clip(big, 0, 1) * 255).astype(np.uint8)).save(path / f"voxel-{name}.png")

    if len(report["unsupported"]):
        marks = report["unsupported"]
        np.save(path / "unsupported.npy", marks)


@njit(cache=True)
def _raster(pix_x, pix_y, depth, faces, vcol, ndot, zbuf, img, size):
    nfaces = faces.shape[0]
    for ti in range(nfaces):
        if ndot[ti] <= 0.05:
            continue
        i0 = faces[ti, 0]
        i1 = faces[ti, 1]
        i2 = faces[ti, 2]
        x0 = pix_x[i0]
        y0 = pix_y[i0]
        z0 = depth[i0]
        x1 = pix_x[i1]
        y1 = pix_y[i1]
        z1 = depth[i1]
        x2 = pix_x[i2]
        y2 = pix_y[i2]
        z2 = depth[i2]
        minx = x0
        if x1 < minx:
            minx = x1
        if x2 < minx:
            minx = x2
        maxx = x0
        if x1 > maxx:
            maxx = x1
        if x2 > maxx:
            maxx = x2
        miny = y0
        if y1 < miny:
            miny = y1
        if y2 < miny:
            miny = y2
        maxy = y0
        if y1 > maxy:
            maxy = y1
        if y2 > maxy:
            maxy = y2
        ix0 = int(np.floor(minx))
        ix1 = int(np.ceil(maxx))
        iy0 = int(np.floor(miny))
        iy1 = int(np.ceil(maxy))
        if ix1 < 0 or iy1 < 0 or ix0 >= size or iy0 >= size:
            continue
        if ix0 < 0:
            ix0 = 0
        if iy0 < 0:
            iy0 = 0
        if ix1 >= size:
            ix1 = size - 1
        if iy1 >= size:
            iy1 = size - 1
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if denom > -1e-6 and denom < 1e-6:
            continue
        inv = 1.0 / denom
        c0r = vcol[i0, 0]
        c0g = vcol[i0, 1]
        c0b = vcol[i0, 2]
        c1r = vcol[i1, 0]
        c1g = vcol[i1, 1]
        c1b = vcol[i1, 2]
        c2r = vcol[i2, 0]
        c2g = vcol[i2, 1]
        c2b = vcol[i2, 2]
        for y in range(iy0, iy1 + 1):
            for x in range(ix0, ix1 + 1):
                w0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) * inv
                if w0 < 0.0:
                    continue
                w1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) * inv
                if w1 < 0.0:
                    continue
                w2 = 1.0 - w0 - w1
                if w2 < 0.0:
                    continue
                z = w0 * z0 + w1 * z1 + w2 * z2
                if z > zbuf[y, x]:
                    zbuf[y, x] = z
                    img[y, x, 0] = w0 * c0r + w1 * c1r + w2 * c2r
                    img[y, x, 1] = w0 * c0g + w1 * c1g + w2 * c2g
                    img[y, x, 2] = w0 * c0b + w1 * c1b + w2 * c2b


def render_shaded(meshes, colors, azim_deg, elev_deg, size, simplify=0.0):
    az = np.deg2rad(azim_deg)
    el = np.deg2rad(elev_deg)
    eye = np.array(
        [np.sin(az) * np.cos(el), np.cos(az) * np.cos(el), np.sin(el)],
        dtype=np.float64,
    )
    cam_z = eye / np.linalg.norm(eye)
    up = np.array([0.0, 0.0, 1.0])
    cam_x = np.cross(up, cam_z)
    cam_x /= np.linalg.norm(cam_x)
    cam_y = np.cross(cam_z, cam_x)

    prepared = []
    all_cam = []
    for mesh, color in zip(meshes, colors):
        if simplify > 0:
            # simplify expects a Manifold; meshes here are trimesh
            pass
        v = np.asarray(mesh.vertices, dtype=np.float64)
        f = np.asarray(mesh.faces, dtype=np.int64)
        prepared.append((v, f, np.asarray(color, dtype=np.float64)))
        all_cam.append(v)
    all_v = np.vstack(all_cam)
    target = (all_v.min(0) + all_v.max(0)) / 2.0
    target = target.copy()
    target[2] -= (all_v.max(0)[2] - all_v.min(0)[2]) * 0.04

    def to_cam(v):
        d = v - target
        return np.column_stack((d @ cam_x, d @ cam_y, d @ cam_z))

    cam_all = to_cam(all_v)
    span = cam_all[:, :2].max(0) - cam_all[:, :2].min(0)
    extent = float(max(span))
    margin = extent * 0.12
    scale = (size - 1) / (extent + 2 * margin)
    mid = (cam_all[:, :2].min(0) + cam_all[:, :2].max(0)) / 2.0

    img = np.zeros((size, size, 3), dtype=np.float64)
    yy = np.linspace(0.0, 1.0, size)[:, None]
    bg = np.array([0.965, 0.945, 0.905]) * (1.0 - 0.10 * yy)
    img[:] = bg
    zbuf = np.full((size, size), -1e9, dtype=np.float64)

    key = np.array([-0.35, 0.55, 0.78])
    key /= np.linalg.norm(key)
    fill = np.array([0.6, 0.15, 0.35])
    fill /= np.linalg.norm(fill)

    for v, f, color in prepared:
        tri = v[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        vn = np.zeros_like(v)
        for i in range(3):
            np.add.at(vn, f[:, i], n)
        ln = np.linalg.norm(vn, axis=1)
        ln[ln == 0] = 1
        vn /= ln[:, None]
        ldot = np.clip(vn @ key, 0, 1)
        fdot = np.clip(vn @ fill, 0, 1)
        shade = np.clip(0.22 + 0.70 * ldot + 0.22 * fdot, 0, 1.15)
        vcol = color[None, :] * shade[:, None]
        cam = to_cam(v)
        pix_x = (cam[:, 0] - mid[0]) * scale + size / 2.0
        pix_y = size - 1 - ((cam[:, 1] - mid[1]) * scale + size / 2.0)
        fn = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-9)
        ndot = fn @ cam_z
        _raster(
            np.ascontiguousarray(pix_x),
            np.ascontiguousarray(pix_y),
            np.ascontiguousarray(cam[:, 2]),
            np.ascontiguousarray(f),
            np.ascontiguousarray(vcol),
            np.ascontiguousarray(ndot),
            zbuf,
            img,
            size,
        )
    return np.clip(img, 0, 1)


def label_panel(img: np.ndarray, title: str) -> Image.Image:
    im = Image.fromarray((img * 255).astype(np.uint8))
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, im.width, 36), fill=(245, 240, 230))
    draw.text((14, 8), title, fill=(30, 30, 30))
    return im


def save_shaded(parts: dict[str, mf.Manifold], path: Path, size: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    meshes = []
    colors = []
    for item in PALETTE:
        rgb = hex_to_rgb(item["hex"])
        # Keep a black dragon readable without changing the filament color.
        if float(rgb.sum()) < 0.45:
            rgb = rgb * 0.35 + np.array([0.18, 0.18, 0.2])
        meshes.append(to_trimesh(parts[item["key"]]))
        colors.append(rgb)
    shots = [
        ("front", 0, 12),
        ("three-quarter", 38, 16),
        ("side", 90, 10),
        ("back", 180, 12),
    ]
    panels = []
    for name, az, el in shots:
        img = render_shaded(meshes, colors, az, el, size)
        title = {
            "front": "Front",
            "three-quarter": "Three-quarter",
            "side": "Side",
            "back": "Back",
        }[name]
        panel = label_panel(img, f"Tairn, Sgaeyl, Andarna  ·  {title}")
        panel.save(path / f"{name}.png")
        panels.append(panel)
    legend = color_legend(panels[0].width * 2)
    sheet = Image.new(
        "RGB",
        (panels[0].width * 2, panels[0].height * 2 + legend.height),
        (245, 240, 230),
    )
    sheet.paste(panels[0], (0, 0))
    sheet.paste(panels[1], (panels[0].width, 0))
    sheet.paste(panels[2], (0, panels[0].height))
    sheet.paste(panels[3], (panels[0].width, panels[0].height))
    sheet.paste(legend, (0, panels[0].height * 2))
    sheet.save(path / "turnaround.png")


def color_legend(width: int) -> Image.Image:
    im = Image.new("RGB", (width, 54), (245, 240, 230))
    draw = ImageDraw.Draw(im)
    slot_w = width // len(PALETTE)
    for i, item in enumerate(PALETTE):
        x = i * slot_w + 16
        rgb = tuple(int(item["hex"][j : j + 2], 16) for j in (1, 3, 5))
        draw.rounded_rectangle((x, 14, x + 26, 40), radius=4, fill=rgb)
        draw.text((x + 36, 18), f"Slot {item['slot']}  {item['name']}", fill=(30, 30, 30))
    return im


def measure(parts: dict[str, mf.Manifold]) -> dict:
    out = {"parts": {}, "solid_volume_cm3": 0.0, "approx_filament_g": 0.0}
    boxes = []
    for item in PALETTE:
        solid = parts[item["key"]]
        bb = solid.bounding_box()
        boxes.append(bb)
        vol = float(solid.volume())  # mm^3
        area = float(solid.surface_area())
        wall = min(area * 1.2, vol * 0.9)
        printed = wall + max(vol - wall, 0) * 0.12
        grams = printed / 1000.0 * 1.24
        out["parts"][item["key"]] = {
            "name": item["name"],
            "slot": item["slot"],
            "hex": item["hex"],
            "material": item["material"],
            "volume_cm3": round(vol / 1000.0, 2),
            "approx_grams_without_purge": round(grams, 1),
            "triangles": int(solid.num_tri()),
            "components": len(solid.decompose()),
        }
        out["solid_volume_cm3"] += vol / 1000.0
        out["approx_filament_g"] += grams
    bb = (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        min(b[2] for b in boxes),
        max(b[3] for b in boxes),
        max(b[4] for b in boxes),
        max(b[5] for b in boxes),
    )
    out["size_mm"] = {
        "x": round(bb[3] - bb[0], 2),
        "y": round(bb[4] - bb[1], 2),
        "z": round(bb[5] - bb[2], 2),
    }
    out["bbox_min_mm"] = [round(bb[0], 3), round(bb[1], 3), round(bb[2], 3)]
    out["solid_volume_cm3"] = round(out["solid_volume_cm3"], 2)
    out["approx_filament_g"] = round(out["approx_filament_g"], 1)
    out["approx_note"] = (
        "Filament mass is a rough shell-and-infill estimate at 3 walls of 0.4 mm "
        "and 12% infill. It does not include IFS purge. The slicer total is the one to trust."
    )
    return out


def assert_printable(parts: dict[str, mf.Manifold], report, bed=220.0) -> None:
    stats = measure(parts)
    size = stats["size_mm"]
    if size["x"] > bed - 8 or size["y"] > bed - 8 or size["z"] > bed - 8:
        raise RuntimeError(f"model exceeds AD5X bed: {size}")
    if abs(stats["bbox_min_mm"][2]) > 0.05:
        raise RuntimeError(f"sole is not on z=0: {stats['bbox_min_mm']}")
    for key, info in stats["parts"].items():
        if info["volume_cm3"] < 0.4:
            raise RuntimeError(f"{key} is too small to count as a real color ({info['volume_cm3']} cm3)")
    n_bad = len(report["unsupported"])
    if n_bad:
        from scipy import ndimage

        occ_bad = np.zeros(report["volume"].shape[:3], dtype=bool)
        idx = report["unsupported"]
        occ_bad[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        labeled, count = ndimage.label(occ_bad)
        sizes = ndimage.sum(occ_bad, labeled, range(1, count + 1))
        big = [(int(s), int(i + 1)) for i, s in enumerate(np.atleast_1d(sizes)) if s >= 8]
        if big:
            pitch = float(report["pitch"])
            vmin = report["vmin"]
            centers = []
            for size, label in sorted(big, reverse=True)[:6]:
                pts = np.argwhere(labeled == label)
                world = vmin + (pts.mean(0) + 0.5) * pitch
                centers.append([round(float(v), 1) for v in world] + [int(size)])
            raise RuntimeError(f"unsupported clusters (x, y, z, count): {centers}")
    if report["sole_margin_mm"] < 1.0:
        raise RuntimeError(
            f"center of mass is outside the feet (margin {report['sole_margin_mm']:.2f} mm)"
        )


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_binary_stl(mesh: trimesh.Trimesh, path: Path) -> None:
    tri = np.asarray(mesh.triangles, dtype=np.float32)
    n = np.asarray(mesh.face_normals, dtype=np.float32)
    count = tri.shape[0]
    buf = bytearray()
    header = b"Fourth Wing dragons Flashforge AD5X"
    buf += header[:80].ljust(80, b" ")
    buf += struct.pack("<I", count)
    for i in range(count):
        buf += struct.pack("<12fH", *n[i], *tri[i].reshape(-1), 0)
    path.write_bytes(buf)


def _mesh_xml(solid: mf.Manifold, object_id: int, name: str, pid: int, pindex: int) -> str:
    mesh = solid.to_mesh()
    verts = np.asarray(mesh.vert_properties[:, :3])
    faces = np.asarray(mesh.tri_verts, dtype=np.int64)
    v_lines = [
        f'<vertex x="{v[0]:.5f}" y="{v[1]:.5f}" z="{v[2]:.5f}"/>'
        for v in verts
    ]
    t_lines = [f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>' for t in faces]
    return (
        f'<object id="{object_id}" name="{name}" type="model" pid="{pid}" pindex="{pindex}">'
        "<mesh><vertices>"
        + "".join(v_lines)
        + "</vertices><triangles>"
        + "".join(t_lines)
        + "</triangles></mesh></object>"
    )


def write_3mf(parts: dict[str, mf.Manifold], path: Path) -> None:
    keys = [p["key"] for p in PALETTE]
    bases = []
    for item in PALETTE:
        rgb = item["hex"].lstrip("#")
        bases.append(f'<m:base name="{item["name"]}" displaycolor="#{rgb}FF"/>')
    objects = []
    components = []
    for index, item in enumerate(PALETTE):
        oid = index + 2
        objects.append(_mesh_xml(parts[item["key"]], oid, item["name"], pid=1, pindex=index))
        components.append(
            f'<component objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
        )
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">'
        "<metadata name=\"Application\">AD5X-Print-Studio</metadata>"
        "<metadata name=\"Title\">Tairn Sgaeyl Andarna</metadata>"
        "<resources>"
        '<m:basematerials id="1">'
        + "".join(bases)
        + "</m:basematerials>"
        + "".join(objects)
        + '<object id="1" name="Tairn Sgaeyl Andarna" type="model"><components>'
        + "".join(components)
        + "</components></object></resources>"
        '<build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/></build>'
        "</model>"
    )
    part_xml = []
    for index, item in enumerate(PALETTE):
        part_xml.append(
            f'<part id="{index + 2}" subtype="normal_part">'
            f'<metadata key="name" value="{item["name"]}"/>'
            '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
            f'<metadata key="extruder" value="{item["slot"]}"/>'
            '<mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" '
            'facets_reversed="0" backwards_edges="0"/>'
            "</part>"
        )
    model_settings = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
        ' <object id="1">\n'
        '  <metadata key="name" value="Tairn Sgaeyl Andarna"/>\n'
        '  <metadata key="extruder" value="1"/>\n'
        + "\n".join(f"  {line}" for line in part_xml)
        + "\n </object>\n"
        " <plate>\n"
        '  <metadata key="plater_id" value="1"/>\n'
        '  <metadata key="plater_name" value="Tairn Sgaeyl Andarna"/>\n'
        "  <model_instance>\n"
        '   <metadata key="object_id" value="1"/>\n'
        '   <metadata key="instance_id" value="0"/>\n'
        '   <metadata key="identify_id" value="501"/>\n'
        "  </model_instance>\n"
        " </plate>\n</config>\n"
    )
    project_settings = {
        "filament_colour": [p["hex"] for p in PALETTE],
        "filament_type": ["PLA", "PLA", "PLA", "PLA"],
        "filament_diameter": ["1.75", "1.75", "1.75", "1.75"],
        "filament_density": ["1.24", "1.24", "1.24", "1.24"],
        "filament_cost": ["20", "20", "20", "20"],
        "printer_model": "Flashforge AD5X",
        "printer_variant": "0.4",
    }
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '<Default Extension="config" ContentType="text/plain"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        "</Relationships>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model)
        zf.writestr("Metadata/model_settings.config", model_settings)
        zf.writestr(
            "Metadata/project_settings.config",
            json.dumps(project_settings, indent=2),
        )


def self_test() -> None:
    box = mf.Manifold.cube((10, 10, 10), False)
    slab = z_range(box, 4, 7)
    bb = slab.bounding_box()
    if abs(bb[2] - 4) > 1e-3 or abs(bb[5] - 7) > 1e-3:
        raise RuntimeError(f"z_range failed: {bb}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the four-color Fourth Wing dragons.")
    parser.add_argument("--quality", choices=("preview", "final"), default="final")
    parser.add_argument("--render-size", type=int, default=720)
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    self_test()
    set_quality(args.quality)
    print(f"sculpting ({args.quality})...")
    parts = settle_on_bed(assign_colors(build_scene()))
    print("checking support and balance...")
    pitch = 1.05 if args.quality == "preview" else 0.8
    report = voxel_report(parts, pitch=pitch)
    save_voxel_views(report, PREVIEW)
    stats = measure(parts)
    stats["quality"] = args.quality
    stats["unsupported_voxels"] = int(len(report["unsupported"]))
    stats["sole_margin_mm"] = round(float(report["sole_margin_mm"]), 2)
    stats["center_of_mass_mm"] = [round(float(v), 2) for v in report["com"]]
    stats["printer"] = {
        "model": "Flashforge AD5X",
        "build_mm": [220, 220, 220],
        "nozzle_mm": 0.4,
        "filament": "PLA 1.75 mm",
        "ifs_colors": 4,
    }
    print(json.dumps(stats, indent=2))
    assert_printable(parts, report)

    OUT.mkdir(parents=True, exist_ok=True)
    stl_dir = OUT / "stl"
    stl_dir.mkdir(exist_ok=True)
    for item in PALETTE:
        mesh = to_trimesh(parts[item["key"]])
        assert_export_mesh(mesh, item["key"])
        filename = f"0{item['slot']}_{item['key']}.stl"
        write_binary_stl(mesh, stl_dir / filename)
        print(f"wrote {filename}  tris={len(mesh.faces)}")
    write_3mf(parts, OUT / "fourth-wing-dragons-ad5x.3mf")
    (OUT / "print.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(f"wrote {OUT / 'fourth-wing-dragons-ad5x.3mf'}")

    if not args.skip_render:
        print("rendering...")
        save_shaded(parts, PREVIEW, args.render_size)
        print(f"previews in {PREVIEW}")


if __name__ == "__main__":
    main()
