# Card Frame System

High-quality illustrated card frames with **three locked content slots**. Styling can change; region positions cannot.

## Quality bar

Frames must look like premium game / TCG assets (detailed materials, soft shading, fine ornaments) — **not** flat UI shapes or simple gradient chrome.

Reference quality: sakura shrine sample (`samples/sakura-shrine-v1.png`).

## Preserved areas

Locked in `layout.json` (canvas **750×1050**):

| Area | Region IDs | Role |
|------|------------|------|
| 1. Top title box | `title_box` | Card name / title plaque |
| 2. Central art window | `art_window` | Transparent artwork hole |
| 3. Bottom footer | `bottom_left_box` + `bottom_right_box` | Stats / abilities plaques |

## How to request a new frame

Provide design parameters (JSON or chat). Do **not** override geometry.

```json
{
  "id": "storm-rune-v1",
  "theme": "storm",
  "mood": "tempestuous",
  "palette": { "primary": "#4CC9F0", "secondary": "#3A0CA3", "accent": "#F72585" },
  "materials": { "border": "obsidian with storm-etched runes", "panels": "dark metal plaques", "ornament": "lightning veins" },
  "border_style": "runic",
  "side_fill": "lightning along left/right borders",
  "crest": { "motif": "thunderbolt" },
  "prompt_extras": "Premium illustrated TCG frame. Empty plaques. Transparent center."
}
```

Or copy `REQUEST_TEMPLATE.md` / add `frames/params/<id>.json`.

### Generate prompt + finish PNG

```bash
# 1) Build the image prompt from params + locked layout
python3 frames/build_hq_frame.py --params frames/params/sakura-shrine-v1.json --print-prompt

# 2) Generate a high-quality illustration from that prompt (agent / image model)
#    Use frames/overlays/layout-reference.png as a layout reference.

# 3) Punch the art window to exact layout coords and write sample PNG
python3 frames/build_hq_frame.py \
  --params frames/params/sakura-shrine-v1.json \
  --punch path/to/raw.png \
  --preview
```

### Layout wireframe only (not final art)

`generate_frame.py` outputs a crude SVG schematic for checking slot positions. It is **not** the shipping visual style.

## Files

| File | Purpose |
|------|---------|
| `layout.json` | Locked region coordinates |
| `design-params.schema.json` | Allowed design parameter fields |
| `build_hq_frame.py` | Prompt builder + art-hole punch / preview |
| `generate_frame.py` | Low-fidelity layout wireframe SVG |
| `overlays/layout-reference.png` | Layout guide for image models |
| `REQUEST_TEMPLATE.md` | Fill-in template |
| `params/` | Saved design parameter sets |
| `samples/` | Final HQ PNG frames (+ previews) |
| `samples/legacy-svg/` | Old wireframe SVGs (not quality targets) |

## Rules

- Design of panels, borders, crests, and ornaments may change.
- Locations/sizes of preserved regions stay exactly as in `layout.json`.
- `art_window` must be a clear transparent opening after punch.
- No readable text inside plaques in template frames.
- Visual quality must match the sakura / fire HQ samples.
