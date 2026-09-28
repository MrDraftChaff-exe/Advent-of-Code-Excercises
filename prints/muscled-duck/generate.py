#!/usr/bin/env python3
"""Muscled duck for the Flashforge AD5X (4-color IFS).

Builds a standing, support-friendly figurine and splits it into four
manifold shells, one per filament slot:

  1  duck yellow   body, head, arms, tail
  2  orange        bill, legs, webbed feet
  3  black         lifting belt, gloves, eyes
  4  red           posing trunks, sweatband

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
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
PREVIEW = HERE / "preview"

# Intended IFS colors. Remap slots to loaded channels in Flash Studio;
# keep every slot PLA so the temperatures match.
PALETTE = [
    {
        "slot": 1,
        "key": "yellow",
        "name": "Body",
        "detail": "head, torso, arms, tail",
        "hex": "#F5C518",
        "material": "PLA",
    },
    {
        "slot": 2,
        "key": "orange",
        "name": "Bill, legs and feet",
        "detail": "bill, muscular legs, webbed feet",
        "hex": "#FF6A00",
        "material": "PLA",
    },
    {
        "slot": 3,
        "key": "black",
        "name": "Belt, gloves and eyes",
        "detail": "power belt, lifting gloves, eyes",
        "hex": "#1A1A1A",
        "material": "PLA",
    },
    {
        "slot": 4,
        "key": "red",
        "name": "Trunks and sweatband",
        "detail": "posing trunks, forehead sweatband",
        "hex": "#E10600",
        "material": "PLA",
    },
]


def set_quality(name: str) -> None:
    if name == "preview":
        mf.set_min_circular_angle(20.0)
        mf.set_min_circular_edge_length(0.85)
    elif name == "final":
        mf.set_min_circular_angle(10.0)
        mf.set_min_circular_edge_length(0.38)
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


def capsule(a, b, radius) -> mf.Manifold:
    return link(a, radius, b, radius)


# ---------------------------------------------------------------------------
# Sculpt
# ---------------------------------------------------------------------------

def build_foot(side: float) -> mf.Manifold:
    """Flat-soled webbed foot. Local +Y is forward before it is placed."""
    heel = mf.CrossSection.circle(7.2).translate((0.0, -9.0))
    ball_cs = mf.CrossSection.circle(8.0).translate((0.0, 4.0))
    toes = [
        mf.CrossSection.circle(4.3).translate((-6.4, 14.5)),
        mf.CrossSection.circle(4.8).translate((0.0, 17.5)),
        mf.CrossSection.circle(4.3).translate((6.4, 14.5)),
    ]
    outline = mf.CrossSection.batch_hull([heel, ball_cs, *toes])
    sole = mf.Manifold.extrude(outline, 4.2)
    # Soft instep so the foot is not a slab, sole stays flat on z=0.
    instep = ell((0.0, 2.0, 3.2), (8.5, 12.0, 3.4))
    toe_domes = union_all(
        [
            ell((-6.4, 14.2, 3.6), (4.0, 4.6, 2.2)),
            ell((0.0, 17.0, 3.7), (4.4, 5.0, 2.3)),
            ell((6.4, 14.2, 3.6), (4.0, 4.6, 2.2)),
        ]
    )
    foot = (sole + instep + toe_domes).trim_by_plane((0.0, 0.0, 1.0), 0.0)
    # Toe-out stance. Mirror later expects +X to be the right foot.
    pivot = (0.0, 0.0, 0.0)
    foot = (
        foot.translate((-pivot[0], -pivot[1], -pivot[2]))
        .rotate((0.0, 0.0, -side * 12.0))
        .translate((side * 14.0, 1.5, 0.0))
    )
    return foot


def build_leg(side: float) -> mf.Manifold:
    s = side
    ankle = (s * 12.4, 0.4, 6.2)
    calf = (s * 12.2, -3.4, 15.0)
    knee = (s * 11.6, 1.8, 24.5)
    quad = (s * 9.5, 4.8, 34.0)
    inner = (s * 3.6, 1.2, 35.0)
    hip = (s * 8.0, -1.0, 40.0)
    parts = [
        ell(ankle, (5.6, 5.4, 5.2)),
        ell(calf, (6.8, 8.6, 8.4)),
        ell(knee, (6.2, 6.6, 6.4)),
        ell(quad, (11.2, 11.6, 13.0)),
        ell(inner, (8.2, 8.4, 11.5)),
        ell(hip, (9.5, 10.5, 9.5)),
        link(ankle, 5.2, calf, 6.6),
        link(calf, 6.4, knee, 6.0),
        link(knee, 6.2, quad, 10.0),
        link(quad, 9.5, hip, 9.0),
        # Vastus on the front, hamstring up the back so the glutes have meat under them.
        ell((s * 11.5, 9.2, 32.5), (6.8, 6.2, 8.4)),
        # Vertical hamstring. Same back-Y as the calf, so it does not shelf outward.
        link((s * 11.0, -6.5, 18.0), 6.2, (s * 7.5, -6.0, 42.0), 7.0),
    ]
    leg = union_all(parts)
    # Muscle seams. Centers sit just inside the surface.
    seams = union_all(
        [
            capsule((s * 13.5, 9.5, 27.0), (s * 14.0, 8.0, 37.0), 0.85),
            capsule((s * 12.0, -8.5, 12.0), (s * 12.4, -7.0, 20.0), 0.75),
        ]
    )
    return leg - seams


def build_limbs_and_torso():
    """Return uncolored anatomy groups."""
    feet = build_foot(1.0) + build_foot(-1.0)
    legs = build_leg(1.0) + build_leg(-1.0)
    # Steep arch between the thighs. The sloping faces stay under 45 degrees,
    # which a flat crotch shelf would not.
    arch_cs = mf.CrossSection.batch_hull(
        [
            mf.CrossSection.circle(1.2).translate((-13.0, 14.0)),
            mf.CrossSection.circle(1.2).translate((13.0, 14.0)),
            mf.CrossSection.circle(1.0).translate((0.0, 40.0)),
        ]
    )
    crotch_arch = (
        mf.Manifold.extrude(arch_cs, 70.0)
        .rotate((90.0, 0.0, 0.0))
        .translate((0.0, 28.0, 0.0))
    )
    legs = legs - crotch_arch

    # Full hip goes into the trunks. Yellow only keeps the part above the belt,
    # otherwise a crotch plug is left hanging under the arch.
    hip_full = ell((0.0, 1.5, 42.0), (21.0, 14.5, 12.0))
    glute_full_r = ell((7.2, -5.5, 44.0), (7.2, 6.2, 6.5))
    hip = z_range(hip_full, 51.0, 70.0)
    glute_r = z_range(glute_full_r, 51.0, 70.0)
    waist = ell((0.0, -0.5, 50.5), (14.5, 12.5, 8.0))
    chest = ell((0.0, 2.0, 67.0), (20.5, 16.0, 14.5))
    # Bottom pole sits inside the chest so the exposed lat is a wall, not a shelf.
    lat_r = ell((14.8, -0.5, 73.0), (7.2, 6.8, 6.8))
    trap_r = ell((7.0, -1.5, 78.5), (7.5, 7.0, 6.5))
    pec_r = ell((8.8, 13.2, 71.0), (9.0, 7.2, 8.4))
    oblique_r = ell((13.2, 4.5, 62.0), (5.0, 5.0, 6.0))

    torso = union_all(
        [
            hip,
            both(glute_r),
            waist,
            chest,
            both(lat_r),
            both(trap_r),
            both(pec_r),
            both(oblique_r),
        ]
    )

    # Shadow lines that make the physique read at desk distance.
    definition = union_all(
        [
            capsule((0.0, 18.5, 63.0), (0.0, 16.5, 78.5), 1.2),  # sternum
            capsule((-13.0, 17.2, 60.6), (13.0, 17.2, 60.6), 1.0),
            capsule((-12.0, 16.6, 55.0), (12.0, 16.6, 55.0), 0.95),
            capsule((0.0, 17.4, 49.8), (0.0, 16.6, 63.0), 0.85),
        ]
    )
    torso = torso - definition

    neck = ell((0.0, 4.0, 82.0), (9.2, 8.6, 9.0))
    head_c = (0.0, 8.0, 97.0)
    head_r = (16.4, 15.0, 15.2)
    head = ell(head_c, head_r)
    # Heavy brow, tipped down toward the bill. Stays below the sweatband.
    brow_r = ell((6.4, 18.2, 100.2), (7.2, 4.4, 2.8))
    cheek_r = ell((10.0, 15.5, 93.5), (5.8, 4.8, 4.8))
    jaw = ell((0.0, 13.0, 88.5), (11.5, 8.5, 6.8))
    head_group = union_all([head, both(brow_r), both(cheek_r), jaw, neck])

    # Base is buried in the lower back so the tail cannot detach when the
    # trunks take a bite out of the glutes.
    tail = mf.Manifold.batch_hull(
        [
            ell((0.0, -4.0, 62.0), (6.0, 6.5, 6.0)),
            ell((0.0, -12.0, 64.0), (4.4, 4.5, 3.8)),
            ell((0.0, -21.0, 74.0), (2.6, 4.2, 2.0)),
            ell((-2.8, -19.0, 72.5), (1.8, 3.0, 1.5)),
            ell((2.8, -19.0, 72.5), (1.8, 3.0, 1.5)),
        ]
    )

    # Arms hang close to the ribs and end in gloves that sit on the trunks.
    def arm(side: float) -> mf.Manifold:
        s = side
        delt = (s * 24.0, 1.5, 77.0)
        bicep = (s * 23.2, 6.5, 67.5)
        elbow = (s * 20.5, 5.2, 59.5)
        forearm = (s * 18.2, 4.6, 55.5)
        parts = [
            ell(delt, (10.0, 8.4, 8.8)),
            ell(bicep, (7.2, 6.4, 8.4)),
            ell(elbow, (5.6, 5.2, 5.6)),
            ell(forearm, (5.4, 5.0, 5.8)),
            link(delt, 8.6, bicep, 6.8),
            link(bicep, 6.6, elbow, 5.3),
            link(elbow, 5.2, forearm, 5.0),
            ell((s * 25.5, 5.5, 65.5), (3.2, 3.2, 6.5)),
        ]
        return union_all(parts)

    arms = arm(1.0) + arm(-1.0)

    def glove(side: float) -> mf.Manifold:
        s = side
        fist = ell((s * 16.2, 5.2, 51.0), (6.6, 5.6, 5.8))
        cuff = ell((s * 17.6, 4.8, 56.2), (5.8, 5.0, 4.6))
        thumb = ell((s * 11.2, 8.0, 52.0), (3.0, 2.6, 4.0))
        knuckle = union_all(
            [
                ell((s * (16.2 + dx), 9.2, 52.4), (1.6, 1.4, 1.5))
                for dx in (-3.1, -1.0, 1.1, 3.2)
            ]
        )
        hand = union_all(
            [
                fist,
                cuff,
                thumb,
                knuckle,
                link((s * 16.2, 5.2, 51.0), 5.6, (s * 17.6, 4.8, 56.2), 5.0),
            ]
        )
        # Flat cuff bottom sits on the trunks instead of a round overhang.
        hand = z_range(hand, 46.4, 64.0)
        groove = capsule((s * 11.0, 9.0, 56.0), (s * 23.5, 1.5, 56.0), 0.65)
        return hand - groove

    gloves = glove(1.0) + glove(-1.0)

    # Upper bill + heavy lower jaw that lands on the chest.
    bill_upper = mf.Manifold.batch_hull(
        [
            ell((0.0, 18.0, 93.0), (11.0, 7.5, 4.8)),
            ell((0.0, 28.5, 95.2), (9.6, 7.2, 3.8)),
            ell((0.0, 38.0, 97.6), (6.4, 5.2, 2.6)),
        ]
    )
    bill_lower = mf.Manifold.batch_hull(
        [
            ell((0.0, 16.5, 89.0), (9.4, 6.8, 4.0)),
            ell((0.0, 27.0, 91.6), (8.4, 6.2, 3.0)),
            ell((0.0, 35.5, 94.0), (5.8, 4.6, 2.3)),
            # Chin pad buried in the pecs so the jaw is supported.
            ell((0.0, 13.5, 80.0), (8.4, 7.2, 6.8)),
            ell((0.0, 17.5, 84.5), (7.4, 6.4, 5.4)),
        ]
    )
    bill = bill_upper + bill_lower
    # Mouth seam and nostrils. Keep them shallow so the bill stays one piece.
    seam = (
        mf.Manifold.cylinder(46.0, 0.55, 0.55, 20)
        .rotate((0.0, 90.0, 0.0))
        .translate((-20.0, 26.5, 92.8))
    )
    nostrils = union_all(
        [
            mf.Manifold.cylinder(6.0, 1.2, 1.2, 16).translate((s * 3.6, 27.0, 96.2))
            for s in (-1.0, 1.0)
        ]
    )
    bill = bill - seam - nostrils

    # Eyes sit in the front of the skull, big enough for a 0.4 mm nozzle.
    def eye(side: float) -> mf.Manifold:
        return ell((side * 6.8, 19.4, 95.4), (4.0, 3.5, 3.9))

    eyes = eye(1.0) + eye(-1.0)

    # Vertical belt walls. A slice of a rounded waist flares as it rises and
    # prints as a ledge, so the band is an extrusion of the waist outline.
    belt_band = mf.Manifold.extrude(waist.slice(50.5), 8.8).translate((0.0, 0.0, 45.6))
    # Buckle grows forward as it rises, so the face is proud without a ledge.
    buckle = mf.Manifold.batch_hull(
        [
            ell((-5.2, 10.4, 48.8), (1.5, 1.1, 1.1)),
            ell((5.2, 10.4, 48.8), (1.5, 1.1, 1.1)),
            ell((-4.8, 12.6, 54.4), (1.7, 1.2, 1.5)),
            ell((4.8, 12.6, 54.4), (1.7, 1.2, 1.5)),
        ]
    )
    belt = belt_band + buckle

    # Trunks are the hip mass between the legs and the belt, with a high side cut
    # so the outer quad still shows.
    trunk_core = z_range(
        union_all([hip_full, both(glute_full_r), waist, legs]), 28.5, 46.8
    )
    side_cut = union_all(
        [
            ell((s * 20.0, 6.0, 30.5), (10.0, 12.0, 8.0))
            for s in (-1.0, 1.0)
        ]
    )
    trunks = trunk_core - side_cut - crotch_arch

    # The trunks are cut from the same thigh surface. Subtracting that copy
    # leaves vertices stacked on top of each other, and a slicer weld turns
    # those into non-manifold edges. Build the orange thigh directly: the leg
    # below the trunk line, plus the outer quad the side cut leaves exposed.
    leg_body = drop_dust(legs)
    orange_legs = drop_dust(
        z_range(leg_body, -5.0, 28.5)
        + drop_dust(z_range(leg_body, 28.5, 46.8) ^ side_cut)
        + feet
    )

    # Sweatband: forehead slice, stepped outward toward the crown so the lip
    # climbs at a printable angle instead of sticking out as a ledge.
    band_slices = []
    z0, z1 = 102.4, 107.2
    steps = 5
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        grow = 1.0 + 0.05 * (t0 + t1) * 0.5
        grown = (
            head.translate((-head_c[0], -head_c[1], -head_c[2]))
            .scale((grow, grow, 1.0))
            .translate(head_c)
        )
        za = z0 + (z1 - z0) * t0
        zb = z0 + (z1 - z0) * t1 + 0.25
        band_slices.append(z_range(grown, za, zb))
    headband = union_all(band_slices)

    yellow_src = union_all([torso, neck, head_group, tail, arms])
    return {
        "yellow_src": yellow_src,
        "orange_src": orange_legs,
        "black_src": union_all([belt, gloves, eyes]),
        "red_src": union_all([trunks, headband]),
        "bill": bill,
        "eyes": eyes,
    }


def assign_colors(raw: dict) -> dict[str, mf.Manifold]:
    """Give overlaps to the part that should be visible.

    Priority, highest first: eyes and the rest of the black hardware,
    the bill, then red clothing, then orange legs, then the yellow body.
    """
    black = drop_dust(raw["black_src"])
    bill = drop_dust(raw["bill"] - black)
    red = drop_dust(raw["red_src"] - black - bill)
    # The orange thighs already stop at the trunk. Subtracting red or the bill
    # anyway runs the boolean along a shared face and stacks vertices.
    orange = drop_dust(raw["orange_src"] + bill)
    yellow = drop_dust(raw["yellow_src"] - black - red - orange)
    parts = {"yellow": yellow, "orange": orange, "black": black, "red": red}
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

    order = ["yellow", "orange", "red", "black"]
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
    keys = ["yellow", "orange", "black", "red"]
    meshes = []
    colors = []
    for key in keys:
        # Lighten black just enough that form still reads in the preview.
        rgb = hex_to_rgb(next(p["hex"] for p in PALETTE if p["key"] == key))
        if key == "black":
            rgb = rgb * 0.35 + np.array([0.16, 0.16, 0.17])
        meshes.append(to_trimesh(parts[key]))
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
        panel = label_panel(img, f"Muscled duck  ·  {title}")
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
    header = b"Muscled duck Flashforge AD5X"
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
        "<metadata name=\"Title\">Muscled Duck</metadata>"
        "<resources>"
        '<m:basematerials id="1">'
        + "".join(bases)
        + "</m:basematerials>"
        + "".join(objects)
        + '<object id="1" name="Muscled Duck" type="model"><components>'
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
        '  <metadata key="name" value="Muscled Duck"/>\n'
        '  <metadata key="extruder" value="1"/>\n'
        + "\n".join(f"  {line}" for line in part_xml)
        + "\n </object>\n"
        " <plate>\n"
        '  <metadata key="plater_id" value="1"/>\n'
        '  <metadata key="plater_name" value="Muscled Duck"/>\n'
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
    parser = argparse.ArgumentParser(description="Generate the 4-color muscled duck.")
    parser.add_argument("--quality", choices=("preview", "final"), default="final")
    parser.add_argument("--render-size", type=int, default=720)
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    self_test()
    set_quality(args.quality)
    print(f"sculpting ({args.quality})...")
    parts = settle_on_bed(assign_colors(build_limbs_and_torso()))
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
    write_3mf(parts, OUT / "muscled-duck-ad5x.3mf")
    (OUT / "print.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(f"wrote {OUT / 'muscled-duck-ad5x.3mf'}")

    if not args.skip_render:
        print("rendering...")
        save_shaded(parts, PREVIEW, args.render_size)
        print(f"previews in {PREVIEW}")


if __name__ == "__main__":
    main()
