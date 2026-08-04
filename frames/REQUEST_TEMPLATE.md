# New Frame Request

Fill this out and send it (or save as `frames/params/<id>.json` using the schema).

```json
{
  "id": "your-frame-id",
  "theme": "",
  "mood": "",
  "element": "",
  "palette": {
    "primary": "#",
    "secondary": "#",
    "accent": "#",
    "border": "#2A2A2A",
    "panel": "#3A3A3A",
    "panel_stroke": "#",
    "glow": "#"
  },
  "materials": {
    "border": "",
    "panels": "",
    "ornament": ""
  },
  "border_style": "jagged",
  "side_fill": "",
  "crest": {
    "motif": "",
    "placement": ["top", "bottom_center"]
  },
  "title_box_style": "",
  "footer_box_style": "",
  "ornaments": [],
  "constraints": {
    "keep_art_fully_transparent": true,
    "allow_overlap_preserved_regions": false,
    "notes": "Keep title_box, art_window, and bottom boxes exactly on layout.json."
  },
  "prompt_extras": ""
}
```

`border_style` options: `jagged` | `ornate` | `clean` | `runic` | `organic` | `geometric`

## Locked (do not change)

- `title_box`: 140,55 470×70
- `art_window`: 95,145 560×620 (transparent)
- `bottom_left_box`: 95,820 240×140
- `bottom_right_box`: 415,820 240×140
