#!/usr/bin/env python3
"""Export the 200-piece tower set, check it, and pack 220 mm plates."""

import shutil
import struct
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path = [p for p in sys.path if not str(p).startswith("/usr/local/lib/python3.12/dist-packages")]
sys.path.insert(0, "/usr/lib/python3/dist-packages")

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / "scad" / "set200.scad"
STL_DIR = ROOT / "stl"
PLATE_DIR = ROOT / "plates"
IMG_DIR = ROOT / "images"
ART = Path("/opt/cursor/artifacts")
BED = 220.0
MARGIN = 5.0
GAP = 2.8

# Printed pieces. LG is the ball gauge, not one of the 200.
# 80 connectors + 36 tracks + 24 other pieces + 60 bought marbles = 200.
PIECES = [
    ("CN", 80, 1),
    ("L", 8, 3),
    ("M", 8, 3),
    ("S", 6, 3),
    ("CL", 3, 3),
    ("CR", 3, 3),
    ("UT", 2, 3),
    ("SW", 2, 3),
    ("ZZ", 2, 3),
    ("WH", 2, 3),
    ("BF", 8, 1),
    ("VF", 2, 2),
    ("CB", 4, 2),
    ("YS", 2, 4),
    ("MG", 2, 4),
    ("SN", 2, 4),
    ("SF", 4, 2),
    ("LG", 1, 1),
]

CLEAR_MODES = (
    "stack",
    "ringfit",
    "clear",
    "fit",
    "footstack",
    "footring",
    "ysfit",
    "hopfit",
)


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


def components(tris, tol=0.1):
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


def export_piece(piece):
    tmp = STL_DIR / f"{piece}.ascii.stl"
    cmd = ["openscad", "-o", str(tmp), "-D", f'part="{piece}"', str(SCAD)]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    tris = read_stl(tmp)
    tmp.unlink()
    write_binary(STL_DIR / f"{piece}.stl", tris)
    return tris


def pack(entries):
    usable = BED - 2 * MARGIN
    items = []
    for name, tris in entries:
        mn, mx = bbox(tris)
        size = mx - mn
        items.append((name, tris, mn, float(size[0]), float(size[1])))
    items.sort(key=lambda it: max(it[3], it[4]), reverse=True)
    plates = []

    eps = 0.2

    def fits(w, h, x, y, occupied):
        if x + w > usable + eps or y + h > usable + eps:
            return False
        need = GAP - eps
        for ox, oy, ow, oh, _ in occupied:
            if not (x + w + need <= ox or ox + ow + need <= x or y + h + need <= oy or oy + oh + need <= y):
                return False
        return True

    def place_on(plate, item):
        name, tris, mn, w0, h0 = item
        options = [(w0, h0, False), (h0, w0, True)]
        options.sort(key=lambda o: (o[1], o[0]))
        for w, h, rot in options:
            ys = {0.0}
            for ox, oy, ow, oh, _ in plate:
                ys.add(oy)
                ys.add(oy + oh + GAP)
            for y in sorted(ys):
                xs = [0.0]
                for ox, oy, ow, oh, _ in plate:
                    if not (y + h + GAP <= oy + eps or oy + oh + GAP <= y + eps):
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
                raise RuntimeError(f"{item[0]} does not fit a {BED:.0f} mm plate ({item[3]:.0f} x {item[4]:.0f})")
            plates.append(plate)
    return plates


def plate_mesh(plate):
    chunks = []
    for x, y, w, h, (name, tris, mn, rot) in plate:
        local = tris.copy()
        if rot:
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
    fig = plt.figure(figsize=(cols * 3.2, rows * 3.0))
    fig.suptitle(title, fontsize=14)
    for i, (name, tris) in enumerate(images):
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        draw = tris
        if len(draw) > 2200:
            sel = np.linspace(0, len(draw) - 1, 2200).astype(int)
            draw = draw[sel]
        v1 = draw[:, 1] - draw[:, 0]
        v2 = draw[:, 2] - draw[:, 0]
        nrm = np.cross(v1, v2)
        ln = np.linalg.norm(nrm, axis=1)
        ln[ln == 0] = 1
        shade = np.clip(0.35 + 0.6 * (nrm / ln[:, None])[:, 2], 0, 1)
        colors = np.stack([0.25 + 0.5 * shade, 0.45 + 0.35 * shade, 0.72 + 0.2 * shade], axis=1)
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
    fig.savefig(out, dpi=120)
    plt.close(fig)


def render_plates(plates, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = len(plates)
    cols = 4 if n > 4 else n
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(4.3 * cols, 4.5 * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax in axes[n:]:
        ax.axis("off")
    for i, (ax, plate) in enumerate(zip(axes, plates)):
        ax.set_xlim(0, BED)
        ax.set_ylim(0, BED)
        ax.set_aspect("equal")
        ax.add_patch(Rectangle((0, 0), BED, BED, fill=False, lw=1.2, color="#222"))
        ax.add_patch(
            Rectangle((MARGIN, MARGIN), BED - 2 * MARGIN, BED - 2 * MARGIN, fill=False, lw=0.6, ls="--", color="#888")
        )
        for x, y, w, h, (name, tris, mn, rot) in plate:
            ax.add_patch(Rectangle((MARGIN + x, MARGIN + y), w, h, facecolor="#8eb6e0", edgecolor="#1d4e89", lw=0.5))
            if w > 16 and h > 10:
                ax.text(MARGIN + x + w / 2, MARGIN + y + h / 2, name, ha="center", va="center", fontsize=6)
        ax.set_title(f"Plate {i + 1} / {n}    {len(plate)} pieces")
        ax.set_xlabel("mm")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)


def mode_is_empty(mode):
    tmp = STL_DIR / f"_{mode}.stl"
    proc = subprocess.run(
        ["openscad", "-o", str(tmp), "-D", f'mode="{mode}"', str(SCAD)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    blob = proc.stdout + proc.stderr
    empty = "Current top level object is empty" in blob
    if tmp.exists():
        tmp.unlink()
    return empty


def main():
    log = []

    def say(msg):
        print(msg, flush=True)
        log.append(msg)

    STL_DIR.mkdir(parents=True, exist_ok=True)
    for old in STL_DIR.glob("*.stl"):
        old.unlink()

    meshes = {}
    problems = []
    for piece, qty, expect in PIECES:
        say(f"export {piece} x{qty}")
        meshes[piece] = export_piece(piece)

    say("")
    say("part check")
    for piece, qty, expect in PIECES:
        tris = meshes[piece]
        mn, mx = bbox(tris)
        size = mx - mn
        vols = sorted(
            (abs(signed_volume(tris[g])) for g in components(tris) if abs(signed_volume(tris[g])) > 40),
            reverse=True,
        )
        flag = []
        if mn[2] < -0.05:
            flag.append(f"below bed {mn[2]:.2f}")
        if len(vols) != expect:
            flag.append(f"{len(vols)} solids, want {expect}")
        if max(size[0], size[1]) > BED - 8:
            flag.append("larger than 220 bed")
        status = "OK" if not flag else "CHECK " + ", ".join(flag)
        say(f"  {piece:4} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:5.1f} mm  {status}")
        if flag:
            problems.append((piece, flag))

    say("")
    say("fit checks (empty means the parts clear)")
    for mode in CLEAR_MODES:
        empty = mode_is_empty(mode)
        say(f"  {mode:10} {'empty OK' if empty else 'CONTACT FAIL'}")
        if not empty:
            problems.append((mode, ["contact"]))

    entries = []
    for piece, qty, expect in PIECES:
        for _ in range(qty):
            entries.append((piece, meshes[piece]))
    plates = pack(entries)
    say("")
    say(f"full set packs onto {len(plates)} plates of {BED:.0f} x {BED:.0f} mm")
    PLATE_DIR.mkdir(parents=True, exist_ok=True)
    for old in PLATE_DIR.glob("*.stl"):
        old.unlink()
    for i, plate in enumerate(plates, start=1):
        mesh = plate_mesh(plate)
        path = PLATE_DIR / f"set-220-{i:02d}of{len(plates):02d}.stl"
        write_binary(path, mesh)
        names = sorted({item[4][0] for item in plate})
        say(f"  plate {i:02d}: {len(plate):3} pieces  {', '.join(names)}")

    printed = sum(qty for piece, qty, expect in PIECES if piece != "LG")
    say("")
    say(f"printed pieces {printed} + 60 marbles = {printed + 60}")
    say("LG is the gauge card and is not counted in the 200")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    sheet = [(f"{p} x{q}", meshes[p]) for p, q, e in PIECES]
    render_sheet(sheet, IMG_DIR / "parts.png", "200-piece tower set")
    render_plates(plates, IMG_DIR / "plates.png")
    shutil.copy(IMG_DIR / "parts.png", ART / "parts.png")
    shutil.copy(IMG_DIR / "plates.png", ART / "plates.png")

    report = "\n".join(log) + "\n"
    (ROOT / "validation.txt").write_text(report)
    (ART / "kit-validation.txt").write_text(report)
    if problems:
        say("PROBLEMS")
        for name, flags in problems:
            say(f"  {name}: {flags}")
        sys.exit(1)
    say("all checks passed")


if __name__ == "__main__":
    main()
