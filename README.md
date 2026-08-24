# Facts or Whacks — 30s video batch

Turn each topic still (or any folder of images/videos) into a **30-second 9:16 clip** with a trendy-style audio bed underneath.

Licensed TikTok/Reels sounds cannot be bundled here. The script generates an original royalty-free dark-cinematic trap bed timed to 30s (same bed as `canva/audio/royalty_free_30s.mp3`). Do not substitute Canva Pro audio.

## Batch the CSV (all 30 topics)

```bash
python3 scripts/overlay_trendy_audio.py --csv facts-or-whacks-30-videos.csv
```

Writes `output/videos/01-….mp4` through `30-….mp4`.

## Overlay the same 30s bed on your own files

```bash
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips --audio /path/to/your-sound.mp3
```

Images become a Ken Burns 9:16 clip. Videos are fitted to 9:16, trimmed/padded to 30s, and the soundtrack is replaced.

Needs `ffmpeg`, `python3`, `numpy`, `Pillow`, and `xlsxwriter`.

```bash
python3 -m pip install --user pillow numpy xlsxwriter
```

## Canva Business — 392 images → 30s videos with Pro music

This environment has **no Canva MCP and no Canva login**. It cannot open your Canva Business account, Autofill 392 designs, or export MP4s for you. Canva Connect Autofill is **Enterprise-only**; Business is not enough for the API path.

What **does** work on Canva Business is one 30-second video template (music on the template) plus Bulk Create.

### Prepare the pack locally

Drop the 392 images in `canva/inbox/` (jpg/png/webp; files with `-raw` in the name are skipped):

```bash
python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox --csv facts-or-whacks-30-videos.csv
```

That writes `output/canva/`:

- `stills/` — cover-cropped **1080×1920** JPEGs
- `bulk-create-batch-01-of-02.xlsx` (300 rows) and `batch-02` (92 rows)
- matching `.csv` text files
- `template-mock-1080x1920.jpg` — labeled layout guide (not a Canva export)
- `manifest.json`

Images are **embedded in the spreadsheet cells** (`xlsxwriter.embed_image`). Canva ignores photo URLs and floating Excel pictures.

`--max-rows` defaults to **300** (the Apps → Bulk Create cap). Use it to preview a split:

```bash
python3 scripts/prepare_canva_bulk.py --images-dir output/stills --csv facts-or-whacks-30-videos.csv --max-rows 12 --out output/canva-split
```

### Build the template once (Canva desktop)

1. **Create a design** → **Instagram Video** or **TikTok Video** (1080×1920). This must be a **video**, not a static Instagram post.
2. Click the page duration and set it to **30s**.
3. **Elements → Frames** → stretch a frame full-bleed. This is the photo slot. **Animate → Pan and zoom** (Ken Burns) for the full 30s.
4. Add **title** and **hook** text boxes over a dark lower-third. Optional handle `@FactsOrWhacks` at the top.
5. **Elements → Audio** → filter **Pro (crown)** → pick a 30s+ **instrumental**. Trim **0:00–0:30**, fade the last second. Do **not** use Popular / chart tracks.
6. Leave the music **on the template**. Every bulk copy inherits it. Do not map audio as a Bulk Create column.
7. Canva Pro/Business audio is royalty-free under Canva’s Content License **when exported as part of the design**. Each MP4 gets its **own** license.

Field list: `canva/template_spec.json`.

### Bulk Create (392 = two Apps batches, or one Sheet)

**Option A — Apps → Bulk Create (300-row cap)**

1. Apps → **Bulk Create** → **Upload data** → `bulk-create-batch-01-of-02.xlsx`.
2. Connect `image` → frame, `title` → title, `hook` → hook (`handle` optional).
3. Preview **one** row, then generate.
4. Repeat with `bulk-create-batch-02-of-02.xlsx` (92 rows).
5. **Share → Download** each design as **MP4**.

**Option B — Canva Sheets (no 300-row cap)**

1. Canva Sheets → import the xlsx (or both batches into one sheet).
2. Select the data range → **Actions → Bulk Create designs**.
3. Pick the 30s video template. Same field mapping. Generate once for all 392.

Before export: **connect YouTube / Instagram / TikTok** in Canva settings so the Pro-audio license attaches and Content ID claims are easier to clear.

To let an agent drive Canva from Cursor, connect the [official Canva MCP](https://www.canva.dev/docs/mcp/) (Business counts as Pro-and-above for uploads/exports; Autofill of 392 designs via API still needs Enterprise).
