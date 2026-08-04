# Card Frame System

High-quality **frame cutout** assets with locked content slots. Styling can change; region positions cannot.

## Possibility check

| Ask | Possible? | How |
|-----|-----------|-----|
| Fully transparent frame (no backdrop) | Yes | Green-screen / keyed PNG with transparent exterior + art hole |
| Frame only (not a full scene) | Yes | No outer VFX trimming / fire halo / ground plate |
| Editable layers | Yes | Delivered as a **transparent PNG layer pack** + `manifest.json` |

A single generative illustration is flat. Editability comes from exporting region layers (`layers/*.png`) you can open in Photoshop/Aseprite/ Affinity / etc., edit, then recompose.

PSD multi-layer write is not required; PNG layers are the supported portable format.

## Preserved areas

Locked in `layout.json` (canvas **750×1050**):

1. `title_box`
2. `art_window` (transparent)
3. `bottom_left_box` + `bottom_right_box`

## Layer pack layout

```text
frames/samples/<id>/
  frame.psd              # PRIMARY: single editable file (toggle/blend layers)
  frame.ora              # optional GIMP/Krita layered file
  frame.png              # transparent composite
  preview.png
  manifest.json
  layers/*.png           # individual layer PNGs for scripting
```

Open `frame.psd` in Photoshop, Affinity Photo, or Photopea — each layer can be shown/hidden and blend modes/opacity changed.

## Generate a new frame

```bash
python3 frames/build_hq_frame.py --params frames/params/<id>.json --print-prompt
# generate illustrated cutout on green screen from that prompt
python3 frames/export_layers.py --params frames/params/<id>.json --punch path/to/raw.png
```

Constraints for every frame:

- `frame_only: true`
- `transparent_background: true`
- `no_outer_vfx_trimming: true` (no fire sprays / particle halos outside the silhouette)

## Samples

- `frames/samples/fire-lava-v1/` — volcanic frame cutout + layers
- `frames/samples/sakura-shrine-v1/` — sakura frame + layers
