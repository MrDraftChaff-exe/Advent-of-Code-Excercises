# Facts or Whacks — 30s video batch

Turn each topic still (or any folder of images/videos) into a **30-second 9:16 clip** with a **royalty-free** audio bed.

No Canva Pro music and no licensed TikTok/Reels sounds. The repo ships an original 30s bed (`canva/audio/royalty_free_30s.mp3`, CC0). The local renderer generates the same style of original audio.

## Batch the CSV (all 30 topics)

```bash
python3 scripts/overlay_trendy_audio.py --csv facts-or-whacks-30-videos.csv
```

Writes `output/videos/01-….mp4` through `30-….mp4`.

## Overlay the same 30s bed on your own files

```bash
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips --audio canva/audio/royalty_free_30s.mp3
```

Images become a Ken Burns 9:16 clip. Videos are fitted to 9:16, trimmed/padded to 30s, and the soundtrack is replaced.

Needs `ffmpeg`, `python3`, `numpy`, `Pillow`, and `xlsxwriter`.

```bash
python3 -m pip install --user pillow numpy xlsxwriter
```

## Canva Business — 392 images → 30s videos (royalty-free audio)

This environment has **no Canva MCP and no Canva login**, so it cannot open your account or export 392 MP4s. Canva Connect Autofill is **Enterprise-only**.

On Canva Business, use **one 30s video template + Bulk Create**. Put **royalty-free** audio on the template — **not** Canva Pro (crown) tracks.

### Prepare the pack locally

Drop the 392 images in `canva/inbox/` (jpg/png/webp; files with `-raw` in the name are skipped):

```bash
python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox
```

That writes `output/canva/`:

- `stills/` — cover-cropped **1080×1920** JPEGs
- `bulk-create-batch-01-of-02.xlsx` (300 rows) and `batch-02` (92 rows)
- matching `.csv` text files
- `royalty_free_30s.mp3` — original CC0 bed (also at `canva/audio/royalty_free_30s.mp3`)
- `template-mock-1080x1920.jpg` — labeled layout guide (not a Canva export)
- `manifest.json`

Images are **embedded in the spreadsheet cells**. Canva ignores photo URLs.

`--max-rows` defaults to **300** (the Apps → Bulk Create cap).

### Build the template once (Canva desktop)

1. **Create a design** → **Instagram Video** or **TikTok Video** (1080×1920). Must be a **video**, not a static post.
2. Set page duration to **30s**.
3. **Elements → Frames** → full-bleed frame. **Animate → Pan and zoom** for 30s.
4. Add **title** and **hook** text over a dark lower-third.
5. **Uploads** → upload `canva/audio/royalty_free_30s.mp3` (or any CC0 / Pixabay / Mixkit / YouTube Audio Library track you have rights to). Place it on the timeline, trim **0:00–0:30**, fade the last second.
6. Do **not** use **Elements → Audio → Pro (crown)** or Popular/chart songs.
7. Leave the uploaded track **on the template** so every bulk copy inherits it. Do not map audio as a Bulk Create column.

License for the shipped bed: `canva/audio/LICENSE.txt`. Field list: `canva/template_spec.json`.

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

To let an agent drive Canva from Cursor, connect the [official Canva MCP](https://www.canva.dev/docs/mcp/). Autofill of 392 designs via API still needs Enterprise.
