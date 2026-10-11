#!/usr/bin/env python3
"""Export the marble kit, check it, and pack starter plates."""

import struct
import subprocess
import sys
from pathlib import Path

sys.path = [p for p in sys.path if not str(p).startswith("/usr/local/lib/python3.12/dist-packages")]
sys.path.insert(0, "/usr/lib/python3/dist-packages")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import PIECES, PART_IDS

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / "scad" / "marble_kit.scad"
STL_DIR = ROOT / "stl"
PLATE_DIR = ROOT / "plates"
IMG_DIR = ROOT / "images"
ART = Path("/opt/cursor/artifacts")
BED = 220.0
MARGIN = 5.0
GAP = 2.8


def read_stl(path):
    data = Path(path).read_bytes()
    if data[:5].lower() == b"solid" and b"facet" in data[:400]:
        verts = []
        cur = []
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                cur.append([float(x) for x in line.split()[1:4]])
                if len(cur) == 3:
                    verts.append(cur)
                    cur = []
        return np.asarray(verts, dtype=np.float64) if verts else np.zeros((0, 3, 3))
    n = struct.unpack_from("<I", data, 80)[0]
    tris = np.zeros((n, 3, 3), dtype=np.float64)
    off = 84
    for i in range(n):
        nums = struct.unpack_from("<12fH", data, off)
        tris[i, 0] = nums[3:6]
        tris[i, 1] = nums[6:9]
        tris[i, 2] = nums[9:12]
        off += 50
    return tris


def write_binary(path, tris):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(tris)
    out = bytearray(84 + n * 50)
    out[:5] = b"solid"
    struct.pack_into("<I", out, 80, n)
    off = 84
    v1 = tris[:, 1] - tris[:, 0]
    v2 = tris[:, 2] - tris[:, 0]
    normals = np.cross(v1, v2)
    ln = np.linalg.norm(normals, axis=1)
    ln[ln == 0] = 1
    normals = normals / ln[:, None]
    for i in range(n):
        struct.pack_into(
            "<12fH",
            out,
            off,
            *normals[i],
            *tris[i, 0],
            *tris[i, 1],
            *tris[i, 2],
            0,
        )
        off += 50
    path.write_bytes(out)


def bbox(tris):
    pts = tris.reshape(-1, 3)
    return pts.min(0), pts.max(0)


def signed_volume(tris):
    v1, v2, v3 = tris[:, 0], tris[:, 1], tris[:, 2]
    return float(np.sum(np.einsum("ij,ij->i", v1, np.cross(v2, v3))) / 6.0)


def components(tris, tol=0.08):
    from collections import defaultdict

    pts = tris.reshape(-1, 3)
    q = np.round(pts / tol).astype(np.int64)
    vert_tris = defaultdict(list)
    keys = []
    n = len(tris)
    for i in range(n):
        ks = []
        for k in range(3):
            key = tuple(int(x) for x in q[i * 3 + k])
            ks.append(key)
            vert_tris[key].append(i)
        keys.append(ks)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for key in keys[i]:
            for j in vert_tris[key]:
                if j > i:
                    union(i, j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return list(groups.values())


def cg_of(tris):
    v1, v2, v3 = tris[:, 0], tris[:, 1], tris[:, 2]
    vol = np.einsum("ij,ij->i", v1, np.cross(v2, v3)) / 6.0
    cent = (v1 + v2 + v3) / 4.0
    total = float(vol.sum())
    cg = (cent * vol[:, None]).sum(0) / total
    return cg, total


def overhang_area(tris, limit_deg=42):
    v1 = tris[:, 1] - tris[:, 0]
    v2 = tris[:, 2] - tris[:, 0]
    n = np.cross(v1, v2)
    area = 0.5 * np.linalg.norm(n, axis=1)
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1
    n = n / ln[:, None]
    tilt = np.degrees(np.arctan2(np.hypot(n[:, 0], n[:, 1]), -n[:, 2]))
    # Faces sitting on the bed are not overhangs.
    zmax = tris[:, :, 2].max(axis=1)
    on_bed = zmax <= (tris[:, :, 2].min() + 0.45)
    bad = (n[:, 2] < -0.08) & (tilt < limit_deg) & (area > 0.4) & (~on_bed)
    return float(area[bad].sum())


def export_piece(piece, qty):
    STL_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STL_DIR / f"{piece}.ascii.stl"
    cmd = [
        "openscad",
        "-o",
        str(tmp),
        "-D",
        f'part="{piece}"',
        "-D",
        f"mark_qty={qty}",
        str(SCAD),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    tris = read_stl(tmp)
    tmp.unlink()
    out = STL_DIR / f"{piece}.stl"
    write_binary(out, tris)
    return tris


def pack(entries):
    """entries: list of (name, tris). Returns list of plates, each a list of placements."""
    usable = BED - 2 * MARGIN
    items = []
    for name, tris in entries:
        mn, mx = bbox(tris)
        size = mx - mn
        items.append((name, tris, mn, float(size[0]), float(size[1])))
    items.sort(key=lambda it: max(it[3], it[4]), reverse=True)
    plates = []

    def fits(w, h, x, y, occupied):
        if x + w > usable + 1e-6 or y + h > usable + 1e-6:
            return False
        for ox, oy, ow, oh, _ in occupied:
            if not (x + w + GAP <= ox or ox + ow + GAP <= x or y + h + GAP <= oy or oy + oh + GAP <= y):
                return False
        return True

    def place_on(plate, item):
        name, tris, mn, w0, h0 = item
        options = [(w0, h0, False), (h0, w0, True)]
        options.sort(key=lambda o: (o[1], o[0]))
        # Try existing shelves first (lowest y that fits).
        for w, h, rot in options:
            ys = {0.0}
        for ox, oy, ow, oh, _ in plate:
            ys.add(round(oy, 3))
            ys.add(round(oy + oh + GAP, 3))
        for y in sorted(ys):
                xs = [0.0]
                for ox, oy, ow, oh, _ in plate:
                    if not (y + h + GAP <= oy or oy + oh + GAP <= y):
                        xs.append(ox + ow + GAP)
                for x in sorted(xs):
                    if fits(w, h, x, y, plate):
                        plate.append((x, y, w, h, (name, tris, mn, rot)))
                        return True
        return False

    for item in items:
        placed = False
        for plate in plates:
            if place_on(plate, item):
                placed = True
                break
        if not placed:
            plate = []
            if not place_on(plate, item):
                raise RuntimeError(f"{item[0]} does not fit a {BED:.0f} mm plate")
            plates.append(plate)
    return plates


def plate_mesh(plate):
    chunks = []
    for x, y, w, h, (name, tris, mn, rot) in plate:
        local = tris.copy()
        if rot:
            # 90° CCW about Z, then shift so min corner is at origin of the cell
            xyz = local.reshape(-1, 3)
            xy = xyz[:, :2] - mn[:2]
            rotated = np.stack([-xy[:, 1], xy[:, 0]], axis=1)
            xyz = xyz.copy()
            xyz[:, 0] = rotated[:, 0]
            xyz[:, 1] = rotated[:, 1]
            xyz[:, 2] = xyz[:, 2] - mn[2]
            rmin = xyz[:, :2].min(0)
            xyz[:, 0] -= rmin[0]
            xyz[:, 1] -= rmin[1]
            local = xyz.reshape(-1, 3, 3)
        else:
            local = local - mn
        local = local + np.array([MARGIN + x, MARGIN + y, 0.0])
        chunks.append(local)
    return np.concatenate(chunks, axis=0)


def render_sheet(images, out, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    cols = 6
    rows = int(np.ceil(len(images) / cols))
    fig = plt.figure(figsize=(cols * 3.1, rows * 2.8))
    fig.suptitle(title, fontsize=14)
    for i, (name, tris) in enumerate(images):
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        draw = tris
        if len(draw) > 2500:
            sel = np.linspace(0, len(draw) - 1, 2500).astype(int)
            draw = draw[sel]
        v1 = draw[:, 1] - draw[:, 0]
        v2 = draw[:, 2] - draw[:, 0]
        nrm = np.cross(v1, v2)
        ln = np.linalg.norm(nrm, axis=1)
        ln[ln == 0] = 1
        shade = np.clip(0.35 + 0.6 * (nrm / ln[:, None])[:, 2], 0, 1)
        colors = np.stack([0.25 + 0.45 * shade, 0.45 + 0.3 * shade, 0.75 + 0.2 * shade], axis=1)
        ax.add_collection3d(Poly3DCollection(draw, facecolors=colors, linewidths=0))
        mn, mx = bbox(tris)
        span = np.maximum(mx - mn, 1)
        ax.set_xlim(mn[0], mx[0])
        ax.set_ylim(mn[1], mx[1])
        ax.set_zlim(mn[2], mx[2])
        try:
            ax.set_box_aspect(span)
        except Exception:
            pass
        ax.view_init(28, -58)
        ax.set_title(name, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110)
    plt.close(fig)


def render_plates(plates, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = len(plates)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.6))
    if n == 1:
        axes = [axes]
    for i, (ax, plate) in enumerate(zip(axes, plates)):
        ax.set_xlim(0, BED)
        ax.set_ylim(0, BED)
        ax.set_aspect("equal")
        ax.add_patch(Rectangle((0, 0), BED, BED, fill=False, lw=1.2, color="#222"))
        ax.add_patch(Rectangle((MARGIN, MARGIN), BED - 2 * MARGIN, BED - 2 * MARGIN, fill=False, lw=0.6, ls="--", color="#888"))
        for x, y, w, h, (name, tris, mn, rot) in plate:
            ax.add_patch(Rectangle((MARGIN + x, MARGIN + y), w, h, facecolor="#8eb6e0", edgecolor="#1d4e89", lw=0.6))
            ax.text(MARGIN + x + w / 2, MARGIN + y + h / 2, name, ha="center", va="center", fontsize=7)
        ax.set_title(f"Plate {i + 1} / {n}   220 mm")
        ax.set_xlabel("mm")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    log = []

    def say(msg):
        print(msg)
        log.append(msg)

    meshes = {}
    for piece, qty, name, parent in PIECES:
        say(f"export {piece} x{qty}")
        meshes[piece] = export_piece(piece, qty)

    say("")
    say("part check")
    problems = []
    for piece, qty, name, parent in PIECES:
        tris = meshes[piece]
        mn, mx = bbox(tris)
        size = mx - mn
        ncomp = len(components(tris))
        oh = overhang_area(tris)
        flag = []
        if mn[2] < -0.05:
            flag.append(f"below bed {mn[2]:.2f}")
        if ncomp != 1:
            flag.append(f"{ncomp} solids")
        if max(size[0], size[1]) > BED - 2:
            flag.append("larger than 220 bed")
        status = "OK" if not flag else "CHECK " + ", ".join(flag)
        say(f"  {piece:6} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:5.1f} mm  overhang {oh:6.0f} mm2  {status}")
        if flag:
            problems.append((piece, flag))

    # Hinge and marble checks on the straight tube.
    say("")
    say("hinge and marble")
    for mode, angle, expect_empty in (
        ("fit", 0, True),
        ("hit", 0, True),
        ("hit", 10, True),
        ("hit", 22, False),
    ):
        tmp = STL_DIR / "_check.stl"
        cmd = ["openscad", "-o", str(tmp), "-D", f'mode="{mode}"', "-D", f"mate_angle={angle}", "-D", 'part="T1"', str(SCAD)]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        empty = "Current top level object is empty" in (proc.stdout + proc.stderr) or not tmp.exists()
        if tmp.exists():
            tmp.unlink()
        ok = empty == expect_empty
        label = "empty" if empty else "contact"
        want = "empty" if expect_empty else "contact"
        say(f"  {mode} {angle}° -> {label} (want {want}) {'OK' if ok else 'FAIL'}")
        if not ok:
            problems.append((f"{mode}{angle}", ["unexpected"]))

    beam = meshes["SW-A"]
    cg, vol = cg_of(beam)
    mass = vol * 1.24e-3
    # Axle is at x=0. Empty should be tail-heavy (cg x > 0). A glass marble in the cup (x≈-18) should flip it.
    empty_torque = cg[0] * mass
    glass = empty_torque + (-18.0) * 5.4
    steel = empty_torque + (-18.0) * 16.7
    say(f"  seesaw empty torque {empty_torque:.1f} g·mm (tail heavy if > 0)")
    say(f"  seesaw with glass marble {glass:.1f} g·mm (tips if < 0)")
    say(f"  seesaw with steel bearing {steel:.1f} g·mm")
    if not (empty_torque > 8 and glass < -8):
        problems.append(("seesaw", [f"torque empty {empty_torque:.1f} glass {glass:.1f}"]))

    say("")
    entries = []
    for piece, qty, name, parent in PIECES:
        for copy in range(qty):
            entries.append((piece if qty == 1 else f"{piece}", meshes[piece]))
    # Distinguish copies in the layout labels by leaving the piece name (repeated is fine).
    plates = pack(entries)
    say(f"starter set packs onto {len(plates)} plates of {BED:.0f} x {BED:.0f} mm")
    PLATE_DIR.mkdir(parents=True, exist_ok=True)
    for old in PLATE_DIR.glob("*.stl"):
        old.unlink()
    for i, plate in enumerate(plates, start=1):
        mesh = plate_mesh(plate)
        path = PLATE_DIR / f"starter-220-{i}of{len(plates)}.stl"
        write_binary(path, mesh)
        names = sorted({item[4][0] for item in plate})
        say(f"  plate {i}: {len(plate)} pieces, {path.name}")
        say(f"    {', '.join(names)}")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    sheet_items = [(piece, meshes[piece]) for piece, qty, name, parent in PIECES]
    render_sheet(sheet_items, IMG_DIR / "parts.png", "Marble kit parts")
    render_plates(plates, IMG_DIR / "plates.png")
    (IMG_DIR / "parts.png").replace(IMG_DIR / "parts.png")
    import shutil
    shutil.copy(IMG_DIR / "parts.png", ART / "parts.png")
    shutil.copy(IMG_DIR / "plates.png", ART / "plates.png")

    report = ART / "kit-validation.txt"
    report.write_text("\n".join(log) + "\n")
    (ROOT / "validation.txt").write_text("\n".join(log) + "\n")
    say("")
    if problems:
        say("PROBLEMS")
        for name, flags in problems:
            say(f"  {name}: {flags}")
        sys.exit(1)
    say("all checks passed")


if __name__ == "__main__":
    main()
