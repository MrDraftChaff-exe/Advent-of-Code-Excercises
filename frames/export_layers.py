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


def compose_layers(layer_imgs: dict[str, Image.Image], layout: dict[str, Any]) -> Image.Image:
    w, h = layout["canvas"]["width"], layout["canvas"]["height"]
    comp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for name in LAYER_ORDER:
        if name in layer_imgs:
            layer = layer_imgs[name].convert("RGBA")
            if layer.size != (w, h):
                layer = layer.resize((w, h), Image.Resampling.LANCZOS)
            comp = Image.alpha_composite(comp, layer)
    return comp


def export_pack(
    frame_rgba: Image.Image,
    layout: dict[str, Any],
    params: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    layers_dir = out_dir / "layers"
    layers_dir.mkdir(exist_ok=True)

    # Only clear empty fill (green/white). Never hard-wipe the art rect.
    punched = punch_art_hole(frame_rgba, layout, preserve_frame_detail=True)
    punched_arr = clear_outside_silhouette(np.array(punched))
    punched = Image.fromarray(punched_arr, "RGBA")

    layer_imgs = split_layers(punched, layout)
    for name, img in layer_imgs.items():
        img.save(layers_dir / f"{name}.png")

    composed = compose_layers(layer_imgs, layout)
    composed.save(out_dir / "frame.png")
    make_preview_with_checker(composed, layout).save(out_dir / "preview.png")

    # Layered TIFF is optional; Pillow/libtiff multi-page RGBA can fail on some builds.
    tiff_path = out_dir / "frame_layers.tif"
    tiff_ok = False
    try:
        pil_layers = [layer_imgs[name] for name in LAYER_ORDER]
        pil_layers[0].save(
            tiff_path,
            save_all=True,
            append_images=pil_layers[1:],
            format="TIFF",
        )
        tiff_ok = True
    except Exception as exc:  # noqa: BLE001 - optional export
        if tiff_path.exists():
            tiff_path.unlink()
        tiff_ok = False
        tiff_error = str(exc)

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
                "blend": "normal",
                "visible": True,
            }
            for name in LAYER_ORDER
        ],
        "outputs": {
            "composite_png": "frame.png",
            "preview_png": "preview.png",
            "layered_tiff": "frame_layers.tif" if tiff_ok else None,
        },
        "notes": [
            "Edit any layers/*.png independently, then rerun with --compose-only to rebuild frame.png.",
            "Art window and exterior remain fully transparent.",
            "A flat generative illustration is split into editable region layers; this is possible and is the supported edit workflow.",
            "PSD export is not required; transparent PNG layers are the portable editable format.",
        ],
    }
    if not tiff_ok:
        manifest["notes"].append(f"Layered TIFF skipped: {tiff_error}")
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
        print(f"Recomposed {out_dir / 'frame.png'}")
        return

    manifest = export_pack(Image.open(args.punch), layout, params, out_dir)
    print(json.dumps({"out_dir": str(out_dir), "layers": manifest["layer_order"]}, indent=2))


if __name__ == "__main__":
    main()
