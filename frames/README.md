# Card Frame System

Generate themed card frames that keep three content areas locked in place. Styling can change; region positions cannot.

## Preserved areas

From the reference fire frame, these stay fixed (see `layout.json`):

| Area | Region IDs | Role |
|------|------------|------|
| 1. Top title box | `title_box` | Card name / title |
| 2. Central art window | `art_window` | Primary artwork (transparent hole) |
| 3. Bottom footer | `bottom_left_box` + `bottom_right_box` | Stats / abilities / secondary text |

Canvas: **750×1050** (5:7).

## How to request a new frame

1. Copy `params.example.json` to something like `params/my-theme.json`.
2. Edit design fields only (`theme`, `palette`, `materials`, `border_style`, etc.).
3. Do **not** add `x` / `y` / `width` / `height` or region geometry — those come from `layout.json`.
4. Generate:

```bash
python3 frames/generate_frame.py --params frames/params/my-theme.json
python3 frames/generate_frame.py --params frames/params/my-theme.json --guide
```

Or ask in chat with parameters, for example:

```text
Generate a frame using these params:
theme: ice
mood: serene
palette.primary: #7BDFF2
palette.secondary: #1B4965
palette.accent: #CAE9FF
palette.panel: #243B4A
palette.panel_stroke: #7BDFF2
border_style: ornate
side_fill: ice veins / frost
crest.motif: snowflake
materials.border: frost crystal
```

The generator (or AI redesign) must keep all preserved regions at the coordinates in `layout.json`.

## Files

| File | Purpose |
|------|---------|
| `layout.json` | Locked region coordinates |
| `design-params.schema.json` | Allowed design parameter fields |
| `params.example.json` | Fire/lava example matching the reference spirit |
| `generate_frame.py` | SVG frame generator (style-flexible, layout-locked) |
| `overlays/layout-guide.svg` | Visual map of locked regions |
| `REQUEST_TEMPLATE.md` | Fill-in template for new designs |
| `samples/` | Generated outputs |

## Rules

- Design of panels, borders, crests, and ornaments may change.
- Locations and sizes of the preserved regions must stay exactly as in `layout.json`.
- `art_window` must remain a clear transparent opening.
- Decorations may sit between the two bottom boxes (center crest/peak) but must not cover the locked boxes.
