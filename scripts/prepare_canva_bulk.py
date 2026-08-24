#!/usr/bin/env python3
"""Prepare a Canva Business Bulk Create pack: 9:16 stills + batched .xlsx.

Canva Apps → Bulk Create accepts at most 300 rows per run. This script
cover-crops images to 1080x1920 and writes .xlsx files with *in-cell*
embedded images (Canva ignores image URLs and floating Excel pictures).

  python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox
  python3 scripts/prepare_canva_bulk.py --images-dir output/stills --csv facts-or-whacks-30-videos.csv
  python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox --max-rows 300

Then in Canva (desktop, Business):
  1. Create a 1080x1920 *video* (not a static post), page duration 30s.
  2. Full-bleed frame + title/hook text + Pro (crown) audio trimmed to 30s.
  3. Apps → Bulk Create → Upload data → pick batch-01.xlsx (max 300 rows).
  4. Repeat for batch-02.xlsx if you have more than 300 images.
  5. Export each design as MP4. Connect social accounts first so the
     Canva Pro-audio license travels with the file.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from xlsxwriter import Workbook

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1080
HEIGHT = 1920
CANVA_APP_ROW_LIMIT = 300
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
HANDLE = "@FactsOrWhacks"
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_SANS = Path("/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf")


def slug(text: str) -> str:
    keep: list[str] = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif keep and keep[-1] != "-":
            keep.append("-")
    return "".join(keep).strip("-")[:60] or "image"


def cover_crop(src: Path, dest: Path) -> Path:
    im = Image.open(src)
    im = ImageOps.exif_transpose(im) or im
    im = im.convert("RGB")
    scale = max(WIDTH / im.width, HEIGHT / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - WIDTH) // 2
    top = max(0, min(int((nh - HEIGHT) * 0.28), nh - HEIGHT))
    cropped = im.crop((left, top, left + WIDTH, top + HEIGHT))
    cropped = ImageEnhance.Contrast(cropped).enhance(1.06)
    cropped = ImageEnhance.Color(cropped).enhance(0.95)
    cropped = ImageEnhance.Brightness(cropped).enhance(0.94)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest, format="JPEG", quality=88, optimize=True)
    return dest


def load_csv_metadata(csv_path: Path) -> dict[str, dict]:
    """Map topic number / slug / filename hints to title+hook."""
    meta: dict[str, dict] = {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            title = (row.get("title") or "").strip()
            hook = (row.get("hook") or "").strip()
            rec = {"title": title, "hook": hook, "handle": HANDLE}
            num = (row.get("topic_number") or "").strip()
            if num.isdigit():
                n = str(int(num))
                for key in (n, n.zfill(2), n.zfill(3)):
                    meta[key] = rec
            if title:
                meta[slug(title)] = rec
    return meta


def metadata_for(path: Path, meta: dict[str, dict]) -> dict:
    stem = path.stem
    m = re.match(r"^(\d{1,4})", stem)
    if m:
        raw = m.group(1)
        keys = [raw, raw.zfill(2), raw.zfill(3)]
        if raw.isdigit():
            keys.append(str(int(raw)))
        for key in keys:
            if key in meta:
                return dict(meta[key])
    s = slug(stem)
    for key, rec in meta.items():
        if key and not key.isdigit() and key in s:
            return dict(rec)
    pretty = re.sub(r"^\d+[-_]*", "", stem).replace("-", " ").replace("_", " ").strip()
    return {"title": pretty.title() or stem, "hook": pretty.title(), "handle": HANDLE}


def collect_images(images_dir: Path) -> list[Path]:
    files = sorted(
        p
        for p in images_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and "-raw" not in p.stem
    )
    if not files:
        raise SystemExit(f"No images in {images_dir} (skipped *-raw.* files)")
    return files


def write_xlsx(rows: list[dict], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook(str(dest))
    ws = wb.add_worksheet("bulk")
    header = wb.add_format({"bold": True, "bg_color": "#111111", "font_color": "#FFFFFF"})
    text = wb.add_format({"text_wrap": True, "valign": "vcenter"})
    columns = ["title", "hook", "handle", "filename", "image"]
    widths = [28, 42, 18, 36, 18]
    for i, (name, width) in enumerate(zip(columns, widths)):
        ws.write(0, i, name, header)
        ws.set_column(i, i, width)
    ws.set_row(0, 22)
    for r, row in enumerate(rows, start=1):
        ws.set_row(r, 120)
        ws.write(r, 0, row["title"], text)
        ws.write(r, 1, row["hook"], text)
        ws.write(r, 2, row["handle"], text)
        ws.write(r, 3, row["filename"], text)
        # Place-in-cell image (Office 365). Canva Bulk Create ignores URLs
        # and floating insert_image() pictures.
        ws.embed_image(r, 4, row["still"], {"description": row["filename"]})
    wb.close()


def write_text_csv(rows: list[dict], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["title", "hook", "handle", "filename"])
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in ["title", "hook", "handle", "filename"]})


def _font(path: Path, size: int) -> ImageFont.ImageFont:
    if path.is_file():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def write_template_mock(still: Path, dest: Path, title: str, hook: str, handle: str) -> Path:
    """Labeled 1080x1920 still showing where Canva layers should sit."""
    im = Image.open(still).convert("RGB")
    if im.size != (WIDTH, HEIGHT):
        im = im.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, 220):
        a = int(140 * (1 - y / 220))
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))
    for y in range(HEIGHT - 780, HEIGHT):
        t = (y - (HEIGHT - 780)) / 780
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, int(200 * t)))
    draw.rounded_rectangle([36, 36, WIDTH - 36, 150], radius=16, outline=(255, 255, 255, 90), width=2)
    draw.rounded_rectangle([36, HEIGHT - 280, WIDTH - 36, HEIGHT - 36], radius=16, outline=(255, 220, 80, 160), width=2)
    serif = _font(FONT_SERIF, 48)
    sans = _font(FONT_SANS, 32)
    small = _font(FONT_SANS, 24)
    draw.text((WIDTH // 2, 64), handle, font=sans, fill=(255, 255, 255, 230), anchor="mt")
    draw.text((WIDTH // 2, 108), "handle  →  Bulk Create column `handle`", font=small, fill=(200, 200, 200, 220), anchor="mt")
    y = 1320
    draw.rounded_rectangle([80, y, WIDTH - 80, y + 88], radius=12, fill=(0, 0, 0, 160))
    draw.text((WIDTH // 2, y + 20), title[:42] or "TITLE", font=serif, fill=(255, 255, 255, 255), anchor="mt")
    y = 1420
    draw.rounded_rectangle([80, y, WIDTH - 80, y + 72], radius=12, fill=(0, 0, 0, 150))
    draw.text((WIDTH // 2, y + 18), hook[:48] or "HOOK", font=sans, fill=(255, 255, 255, 245), anchor="mt")
    y = 1510
    draw.text((WIDTH // 2, y), "title / hook  →  Bulk Create text fields", font=small, fill=(200, 200, 200, 220), anchor="mt")
    draw.text((WIDTH // 2, HEIGHT - 210), "AUDIO ON TEMPLATE (not a data column)", font=sans, fill=(255, 220, 80, 255), anchor="mt")
    draw.text(
        (WIDTH // 2, HEIGHT - 160),
        "Elements → Audio → Pro (crown)  •  trim 0:00–0:30  •  skip Popular",
        font=small,
        fill=(255, 240, 180, 230),
        anchor="mt",
    )
    draw.text(
        (WIDTH // 2, HEIGHT - 112),
        "1080×1920 video  •  30s  •  Frame = Bulk Create `image`",
        font=small,
        fill=(220, 220, 220, 220),
        anchor="mt",
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB").save(
        dest, format="JPEG", quality=86, optimize=True
    )
    return dest


def batched(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--images-dir",
        dest="images_dir",
        type=Path,
        required=True,
        help="Folder of source images. Files whose stem contains -raw are skipped.",
    )
    p.add_argument(
        "--csv",
        dest="csv_path",
        type=Path,
        help="Optional metadata CSV with title/hook/topic_number columns.",
    )
    p.add_argument(
        "--out",
        dest="out_dir",
        type=Path,
        default=ROOT / "output" / "canva",
        help="Output folder for stills, xlsx batches, csv, and manifest.",
    )
    p.add_argument(
        "--max-rows",
        dest="max_rows",
        type=int,
        default=CANVA_APP_ROW_LIMIT,
        help=f"Rows per xlsx (Canva Apps → Bulk Create cap is {CANVA_APP_ROW_LIMIT}).",
    )
    p.add_argument("--handle", dest="handle", default=HANDLE)
    p.add_argument(
        "--no-mock",
        dest="no_mock",
        action="store_true",
        help="Skip writing the labeled 1080x1920 template mock JPEG.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_rows < 1:
        raise SystemExit("--max-rows must be >= 1")
    images_dir = args.images_dir.resolve()
    if not images_dir.is_dir():
        raise SystemExit(f"Not a directory: {images_dir}")
    meta = load_csv_metadata(args.csv_path.resolve()) if args.csv_path else {}
    files = collect_images(images_dir)
    still_dir = args.out_dir / "stills"
    rows: list[dict] = []
    print(f"Preparing {len(files)} images for Canva Bulk Create…", flush=True)
    for i, src in enumerate(files, 1):
        info = metadata_for(src, meta)
        info["handle"] = args.handle
        dest = still_dir / f"{i:03d}-{slug(info['title'])}.jpg"
        cover_crop(src, dest)
        rows.append(
            {
                "title": info["title"],
                "hook": info["hook"],
                "handle": info["handle"],
                "filename": dest.name,
                "still": str(dest.resolve()),
            }
        )
        if i % 25 == 0 or i == len(files):
            print(f"  {i}/{len(files)} cropped", flush=True)

    batches = batched(rows, args.max_rows)
    manifest = {
        "image_count": len(rows),
        "batch_size": args.max_rows,
        "batch_count": len(batches),
        "canva_apps_row_limit": CANVA_APP_ROW_LIMIT,
        "template": str(ROOT / "canva" / "template_spec.json"),
        "still_size": f"{WIDTH}x{HEIGHT}",
        "image_column": "xlsxwriter embed_image (Place in Cell)",
        "batches": [],
    }
    for b, chunk in enumerate(batches, 1):
        xlsx = args.out_dir / f"bulk-create-batch-{b:02d}-of-{len(batches):02d}.xlsx"
        csv_path = args.out_dir / f"bulk-create-batch-{b:02d}-of-{len(batches):02d}.csv"
        write_xlsx(chunk, xlsx)
        write_text_csv(chunk, csv_path)
        manifest["batches"].append(
            {"xlsx": str(xlsx), "csv": str(csv_path), "rows": len(chunk)}
        )
        print(f"Wrote {xlsx.name} ({len(chunk)} rows)", flush=True)

    mock_path = None
    if not args.no_mock and rows:
        mock_path = args.out_dir / "template-mock-1080x1920.jpg"
        write_template_mock(
            Path(rows[0]["still"]),
            mock_path,
            rows[0]["title"],
            rows[0]["hook"],
            args.handle,
        )
        manifest["template_mock"] = str(mock_path)
        print(f"Wrote {mock_path.name} (layout guide, not a Canva export)", flush=True)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    image_count = len(rows)
    print()
    print(f"{image_count} images → {len(batches)} Canva upload(s) (max {args.max_rows} rows each).")
    if image_count > CANVA_APP_ROW_LIMIT or args.max_rows < CANVA_APP_ROW_LIMIT:
        print(
            "Canva Apps → Bulk Create caps at 300 rows. Use these batches,\n"
            "or put all rows in one Canva Sheet and run Actions → Bulk Create designs."
        )
    print()
    print("In Canva desktop (Business):")
    print("  1. Create Instagram/TikTok Video 1080×1920. Set page duration to 30s.")
    print("  2. Add a full-bleed Frame. Add title + hook text boxes.")
    print("  3. Elements → Audio → Pro (crown) instrumental. Trim to 30s, fade out.")
    print("     Skip Popular/chart songs. Leave audio on the template (not a data field).")
    print("  4. Apps → Bulk Create → Upload data → bulk-create-batch-01-of-XX.xlsx")
    print("  5. Connect `image` → frame, `title` → title, `hook` → hook. Preview 1 row.")
    print("  6. Generate, then export MP4. Repeat for remaining batches.")
    print("  7. Connect YouTube/Instagram/TikTok before export so Pro-audio licenses attach.")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
