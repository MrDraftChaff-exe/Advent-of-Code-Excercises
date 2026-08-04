#!/usr/bin/env python3
"""Export / compose editable transparent frame layers.

Possibility note
----------------
A single generative illustration is flat. Editable layers ARE possible when we
deliver a layered package:
  - transparent PNG per layer (always)
  - optional layered TIFF
  - optional PSD when writers are available

Layers are split by locked layout masks + silhouette so plaques, bezel, and
outer chrome can be edited independently, then recomposed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

try:
    from build_hq_frame import (
        DEFAULT_LAYOUT,
        load_json,
        make_preview_with_checker,
        punch_art_hole,
        slugify,
    )
except ImportError:  # when executed as frames/export_layers.py from repo root
    from frames.build_hq_frame import (  # type: ignore
        DEFAULT_LAYOUT,
        load_json,
        make_preview_with_checker,
        punch_art_hole,
        slugify,
    )


LAYER_ORDER = [
    "outer_frame",
    "art_bezel",
    "title_plaque",
    "footer_left",
    "footer_right",
    "crests",
]

# Friendly Photoshop layer names + default blend modes.
LAYER_META = {
    "outer_frame": {"name": "Outer Frame", "blend": "normal", "visible": True, "opacity": 255},
    "art_bezel": {"name": "Art Bezel", "blend": "normal", "visible": True, "opacity": 255},
    "title_plaque": {"name": "Title Plaque", "blend": "normal", "visible": True, "opacity": 255},
    "footer_left": {"name": "Footer Left", "blend": "normal", "visible": True, "opacity": 255},
    "footer_right": {"name": "Footer Right", "blend": "normal", "visible": True, "opacity": 255},
    "crests": {"name": "Crests", "blend": "normal", "visible": True, "opacity": 255},
}


def _blend_mode(name: str):
    from psd_tools.constants import BlendMode

    mapping = {
        "normal": BlendMode.NORMAL,
        "multiply": BlendMode.MULTIPLY,
        "screen": BlendMode.SCREEN,
        "overlay": BlendMode.OVERLAY,
        "soft_light": BlendMode.SOFT_LIGHT,
        "hard_light": BlendMode.HARD_LIGHT,
        "color_dodge": BlendMode.COLOR_DODGE,
        "color_burn": BlendMode.COLOR_BURN,
        "darken": BlendMode.DARKEN,
        "lighten": BlendMode.LIGHTEN,
        "difference": BlendMode.DIFFERENCE,
        "linear_dodge": BlendMode.LINEAR_DODGE,
        "linear_burn": BlendMode.LINEAR_BURN,
    }
    return mapping.get(name, BlendMode.NORMAL)


def write_psd(
    layer_imgs: dict[str, Image.Image],
    layout: dict[str, Any],
    out_path: Path,
    *,
    layer_meta: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write one editable PSD with toggleable / blendable layers."""
    from psd_tools import PSDImage

    meta = layer_meta or LAYER_META
    w, h = layout["canvas"]["width"], layout["canvas"]["height"]
    psd = PSDImage.new("RGBA", (w, h), color=(0, 0, 0, 0))

    # PSD stacks bottom→top in creation order for psd-tools create_pixel_layer.
    for layer_id in LAYER_ORDER:
        if layer_id not in layer_imgs:
            continue
        info = meta.get(layer_id, {})
        img = layer_imgs[layer_id].convert("RGBA")
        if img.size != (w, h):
            img = img.resize((w, h), Image.Resampling.LANCZOS)
        layer = psd.create_pixel_layer(
            img,
            name=str(info.get("name") or layer_id),
            opacity=int(info.get("opacity", 255)),
            blend_mode=_blend_mode(str(info.get("blend", "normal"))),
        )
        layer.visible = bool(info.get("visible", True))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    psd.save(str(out_path))
    return out_path


def _blank(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.uint8)


def _rect_mask(h: int, w: int, box: dict[str, int], inflate: int = 0) -> np.ndarray:
    m = np.zeros((h, w), dtype=bool)
    x0 = max(0, box["x"] - inflate)
    y0 = max(0, box["y"] - inflate)
    x1 = min(w, box["x"] + box["width"] + inflate)
    y1 = min(h, box["y"] + box["height"] + inflate)
    m[y0:y1, x0:x1] = True
    return m


def _ring_mask(h: int, w: int, box: dict[str, int], outer: int = 28, inner_inset: int = 0) -> np.ndarray:
    outer_box = {
        "x": box["x"] - outer,
        "y": box["y"] - outer,
        "width": box["width"] + 2 * outer,
        "height": box["height"] + 2 * outer,
    }
    m = _rect_mask(h, w, outer_box)
    if inner_inset >= 0:
        hole = {
            "x": box["x"] + inner_inset,
            "y": box["y"] + inner_inset,
            "width": box["width"] - 2 * inner_inset,
            "height": box["height"] - 2 * inner_inset,
        }
        if hole["width"] > 0 and hole["height"] > 0:
            m &= ~_rect_mask(h, w, hole)
    return m


def key_green_screen(image: Image.Image, layout: dict[str, Any]) -> Image.Image:
    """Clear pure green-screen pixels only; never rectangular-wipe the bezel.

    Detects the actual green art hole from the image center and flood-fills
    only connected pure-green / empty pixels. Frame chrome that overlaps the
    nominal layout art_window stays opaque.
    """
    from collections import deque

    canvas = layout["canvas"]
    art = layout["preserved_regions"]["art_window"]
    title = layout["preserved_regions"]["title_box"]
    footer = layout["preserved_regions"]["bottom_left_box"]
    arr = np.array(
        image.convert("RGBA").resize((canvas["width"], canvas["height"]), Image.Resampling.LANCZOS)
    ).astype(np.float32)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    pure = (g > 165) & (g > r + 50) & (g > b + 50) & ((g - np.maximum(r, b)) > 50)

    # Detect hole top from green dominance under the title.
    cx0, cx1 = canvas["width"] // 3, (2 * canvas["width"]) // 3
    top = art["y"]
    for y in range(title["y"] + title["height"], footer["y"]):
        if pure[y, cx0:cx1].mean() > 0.55:
            top = y
            break

    out = arr.copy()
    out[pure] = 0
    dom = g - np.maximum(r, b)
    spill = (out[:, :, 3] > 0) & (dom > 12) & (g > r) & (g > b)
    out[:, :, 1][spill] = np.minimum(g[spill], np.maximum(r[spill], b[spill]) + 8)
    out[out[:, :, 3] > 0, 3] = 255
    out[out[:, :, 3] < 12] = 0

    rr, gg, bb, aa = out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3]
    passable = (aa < 8) | ((gg > 165) & (gg > rr + 50) & (gg > bb + 50))
    visited = np.zeros(aa.shape, dtype=bool)
    q: deque[tuple[int, int]] = deque()
    cy = (top + footer["y"]) // 2
    cx = canvas["width"] // 2
    for sy in range(max(top + 10, cy - 80), min(footer["y"] - 10, cy + 80), 8):
        for sx in range(cx - 80, cx + 81, 8):
            if 0 <= sy < canvas["height"] and 0 <= sx < canvas["width"] and passable[sy, sx]:
                visited[sy, sx] = True
                q.append((sx, sy))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < canvas["width"] and 0 <= ny < canvas["height"] and not visited[ny, nx] and passable[ny, nx]:
                visited[ny, nx] = True
                q.append((nx, ny))
    out[visited] = 0
    out[out[:, :, 3] > 0, 3] = 255
    return harden_opaque_alpha(Image.fromarray(out.astype(np.uint8), "RGBA"))


def clear_outside_silhouette(arr: np.ndarray, *, alpha_threshold: int = 20) -> np.ndarray:
    """Keep only connected opaque silhouette; force true transparent exterior."""
    a = arr[:, :, 3]
    # already mostly handled by generation; harden near-black/near-white backdrop leftovers
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    lum = (r + g + b) / 3.0
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    backdrop = ((lum > 235) & (sat < 20)) | ((lum < 18) & (sat < 10) & (a < 250))
    out = arr.copy()
    out[backdrop | (a < alpha_threshold)] = (0, 0, 0, 0)
    return out


def split_layers(frame_rgba: Image.Image, layout: dict[str, Any]) -> dict[str, Image.Image]:
    """Split a transparent frame into editable region layers.

    Important: do NOT hard-wipe the locked art_window rectangle. Ornate bezels
    often sit inside those coordinates; only already-transparent pixels form the
    art hole, so the frame can overlay checker/gray boxing cleanly.
    """
    canvas = layout["canvas"]
    w, h = canvas["width"], canvas["height"]
    arr = np.array(frame_rgba.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS))
    arr = clear_outside_silhouette(arr)
    opaque = arr[:, :, 3] > 20

    regions = layout["preserved_regions"]
    title_m = _rect_mask(h, w, regions["title_box"], inflate=10)
    bl_m = _rect_mask(h, w, regions["bottom_left_box"], inflate=10)
    br_m = _rect_mask(h, w, regions["bottom_right_box"], inflate=10)
    art = regions["art_window"]
    art_m = _rect_mask(h, w, art)
    # Bezel = opaque pixels near/inside the art rect rim + a ring just outside it.
    bezel_m = _ring_mask(h, w, art, outer=34, inner_inset=0) | (art_m & opaque)

    crest_m = np.zeros((h, w), dtype=bool)
    crest_m[0 : regions["title_box"]["y"] + 8, :] = True
    mid_x0 = regions["bottom_left_box"]["x"] + regions["bottom_left_box"]["width"]
    mid_x1 = regions["bottom_right_box"]["x"]
    crest_m[
        regions["bottom_left_box"]["y"] - 40 : regions["bottom_left_box"]["y"]
        + regions["bottom_left_box"]["height"]
        + 10,
        mid_x0:mid_x1,
    ] = True

    layers = {name: _blank(w, h) for name in LAYER_ORDER}

    def assign(name: str, mask: np.ndarray) -> None:
        taken = np.zeros((h, w), dtype=bool)
        for prev in LAYER_ORDER:
            if prev == name:
                break
            taken |= layers[prev][:, :, 3] > 0
        m = mask & opaque & ~taken
        layers[name][m] = arr[m]

    assign("title_plaque", title_m)
    assign("footer_left", bl_m)
    assign("footer_right", br_m)
    assign("crests", crest_m)
    assign("art_bezel", bezel_m)

    taken = np.zeros((h, w), dtype=bool)
    for name in ("title_plaque", "footer_left", "footer_right", "crests", "art_bezel"):
        taken |= layers[name][:, :, 3] > 0
    layers["outer_frame"][opaque & ~taken] = arr[opaque & ~taken]

    return {k: Image.fromarray(v, "RGBA") for k, v in layers.items()}


def harden_opaque_alpha(img: Image.Image) -> Image.Image:
    """Force surviving frame pixels to full opacity so underlays cannot show through."""
    arr = np.array(img.convert("RGBA"))
    arr[arr[:, :, 3] > 0, 3] = 255
    return Image.fromarray(arr, "RGBA")


def compose_layers(layer_imgs: dict[str, Image.Image], layout: dict[str, Any]) -> Image.Image:
    w, h = layout["canvas"]["width"], layout["canvas"]["height"]
    comp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for name in LAYER_ORDER:
        if name in layer_imgs:
            layer = layer_imgs[name].convert("RGBA")
            if layer.size != (w, h):
                layer = layer.resize((w, h), Image.Resampling.LANCZOS)
            comp = Image.alpha_composite(comp, layer)
    return harden_opaque_alpha(comp)


def write_ora(
    layer_imgs: dict[str, Image.Image],
    layout: dict[str, Any],
    out_path: Path,
    *,
    layer_meta: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write OpenRaster (.ora) for GIMP/Krita with toggleable layers."""
    import io
    import zipfile
    import xml.etree.ElementTree as ET

    meta = layer_meta or LAYER_META
    w, h = layout["canvas"]["width"], layout["canvas"]["height"]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    stack = ET.Element("image", {"w": str(w), "h": str(h), "version": "0.0.3"})
    root = ET.SubElement(stack, "stack", {"name": "Frame Layers"})
    # ORA lists top layer first.
    for layer_id in reversed(LAYER_ORDER):
        if layer_id not in layer_imgs:
            continue
        info = meta.get(layer_id, {})
        ET.SubElement(
            root,
            "layer",
            {
                "name": str(info.get("name") or layer_id),
                "src": f"data/{layer_id}.png",
                "composite-op": "svg:src-over",
                "opacity": f"{float(info.get('opacity', 255)) / 255.0:.4f}",
                "visibility": "visible" if info.get("visible", True) else "hidden",
                "x": "0",
                "y": "0",
            },
        )

    xml_bytes = ET.tostring(stack, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        zf.writestr("stack.xml", xml_bytes)
        # mergedimage + thumbnail
        composed = compose_layers(layer_imgs, layout)
        buf = io.BytesIO()
        composed.save(buf, format="PNG")
        zf.writestr("mergedimage.png", buf.getvalue())
        thumb = composed.copy()
        thumb.thumbnail((256, 256))
        tbuf = io.BytesIO()
        thumb.save(tbuf, format="PNG")
        zf.writestr("Thumbnails/thumbnail.png", tbuf.getvalue())
        for layer_id, img in layer_imgs.items():
            lbuf = io.BytesIO()
            img.convert("RGBA").save(lbuf, format="PNG")
            zf.writestr(f"data/{layer_id}.png", lbuf.getvalue())
    return out_path


def export_pack(
    frame_rgba: Image.Image,
    layout: dict[str, Any],
    params: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    layers_dir = out_dir / "layers"
    layers_dir.mkdir(exist_ok=True)

    # Clear pure green only. Never rectangular-wipe layout art_window —
    # that eats ornate bezels/rivets that sit inside those coordinates.
    punched = key_green_screen(frame_rgba, layout)
    punched = harden_opaque_alpha(Image.fromarray(clear_outside_silhouette(np.array(punched)), "RGBA"))

    layer_imgs = split_layers(punched, layout)
    for name, img in layer_imgs.items():
        img.save(layers_dir / f"{name}.png")

    composed = compose_layers(layer_imgs, layout)
    composed.save(out_dir / "frame.png")
    make_preview_with_checker(composed, layout).save(out_dir / "preview.png")

    psd_path = out_dir / "frame.psd"
    write_psd(layer_imgs, layout, psd_path)

    # Optional ORA (GIMP/Krita) alongside PSD for open tooling.
    ora_path = out_dir / "frame.ora"
    ora_ok = False
    try:
        write_ora(layer_imgs, layout, ora_path)
        ora_ok = True
    except Exception as exc:  # noqa: BLE001
        if ora_path.exists():
            ora_path.unlink()
        ora_error = str(exc)

    manifest = {
        "id": params.get("id"),
        "format": "cursor-card-frame-layers-v1",
        "canvas": layout["canvas"],
        "transparent_background": True,
        "editable": True,
        "layer_order": LAYER_ORDER,
        "layers": [
            {
                "id": name,
                "file": f"layers/{name}.png",
                "psd_name": LAYER_META[name]["name"],
                "blend": LAYER_META[name]["blend"],
                "visible": LAYER_META[name]["visible"],
                "opacity": LAYER_META[name]["opacity"],
            }
            for name in LAYER_ORDER
        ],
        "outputs": {
            "composite_png": "frame.png",
            "preview_png": "preview.png",
            "layered_psd": "frame.psd",
            "layered_ora": "frame.ora" if ora_ok else None,
        },
        "notes": [
            "Primary editable file: frame.psd — toggle visibility and blend modes in Photoshop/Affinity/Photopea.",
            "Optional frame.ora for GIMP/Krita.",
            "Individual layers/*.png are also kept for scripting.",
            "Art window and exterior remain fully transparent.",
        ],
    }
    if not ora_ok:
        manifest["notes"].append(f"ORA skipped: {ora_error}")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--punch", type=Path, required=True, help="Raw illustrated frame PNG")
    parser.add_argument("--out-dir", type=Path, help="Output pack directory")
    parser.add_argument("--compose-only", action="store_true", help="Recompose from existing layers/")
    args = parser.parse_args()

    layout = load_json(args.layout)
    params = load_json(args.params)
    frame_id = slugify(params.get("id") or "frame")
    out_dir = args.out_dir or (Path(__file__).resolve().parent / "samples" / frame_id)

    if args.compose_only:
        layer_imgs = {
            name: Image.open(out_dir / "layers" / f"{name}.png")
            for name in LAYER_ORDER
            if (out_dir / "layers" / f"{name}.png").exists()
        }
        composed = compose_layers(layer_imgs, layout)
        composed.save(out_dir / "frame.png")
        make_preview_with_checker(composed, layout).save(out_dir / "preview.png")
        write_psd(layer_imgs, layout, out_dir / "frame.psd")
        try:
            write_ora(layer_imgs, layout, out_dir / "frame.ora")
        except Exception as exc:  # noqa: BLE001
            print(f"ORA skipped: {exc}")
        print(f"Recomposed {out_dir / 'frame.png'} and {out_dir / 'frame.psd'}")
        return

    manifest = export_pack(Image.open(args.punch), layout, params, out_dir)
    print(json.dumps({"out_dir": str(out_dir), "layers": manifest["layer_order"]}, indent=2))


if __name__ == "__main__":
    main()
