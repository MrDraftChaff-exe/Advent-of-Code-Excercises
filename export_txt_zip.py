#!/usr/bin/env python3
"""Export 395 history topics as individual txt files and zip archive."""

import csv
import re
import zipfile
from pathlib import Path

CSV_PATH = Path("/workspace/facts-or-whacks-395-videos.csv")
OUT_DIR = Path("/workspace/facts-or-whacks-txt")
ZIP_PATH = Path("/workspace/facts-or-whacks-395.zip")
ARTIFACT_ZIP = Path("/opt/cursor/artifacts/facts-or-whacks-395.zip")


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def extract_cover_facts(video_prompt: str) -> list[str]:
    if "Cover:" not in video_prompt:
        return []
    cover = video_prompt.split("Cover:", 1)[1]
    if "Tone:" in cover:
        cover = cover.split("Tone:", 1)[0]
    parts = re.split(r"(?<=[.!?])\s+", cover.strip())
    facts = []
    for part in parts:
        part = part.strip().rstrip(".")
        if part and part.lower() not in {"9:16 vertical", "dramatic, fast-paced, documentary style"}:
            if not part.endswith("."):
                part += "."
            facts.append(part[0].upper() + part[1:] if part else part)
    return facts


def bullet_facts(on_screen_bullets: str) -> list[str]:
    facts = []
    for bullet in on_screen_bullets.split("|"):
        text = bullet.strip()
        if not text:
            continue
        if not text.endswith("."):
            text += "."
        facts.append(text)
    return facts


def merge_facts(row: dict) -> list[str]:
    bullets = bullet_facts(row["on_screen_bullets"])
    if bullets:
        return bullets
    return extract_cover_facts(row["video_prompt"])


def build_txt(row: dict) -> str:
    num = int(row["topic_number"])
    title = row["title"]
    lines = [
        f"{num}. {title}",
        f"Image: {row['image_url']}",
        "",
        f"Hook: {row['hook']}",
        "",
    ]
    for fact in merge_facts(row):
        lines.append(fact)
    lines.extend(
        [
            "",
            f"Caption: {row['caption']}",
            "",
            f"Hashtags: {row['hashtags']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.txt"):
        old.unlink()

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        num = int(row["topic_number"])
        filename = f"{num:03d}-{slugify(row['title'])}.txt"
        (OUT_DIR / filename).write_text(build_txt(row), encoding="utf-8")

    ARTIFACT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    for zip_path in (ZIP_PATH, ARTIFACT_ZIP):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for txt in sorted(OUT_DIR.glob("*.txt")):
                zf.write(txt, arcname=f"facts-or-whacks/{txt.name}")

    print(f"Created {len(rows)} txt files in {OUT_DIR}")
    print(f"Zip: {ZIP_PATH} ({ZIP_PATH.stat().st_size // 1024} KB)")
    print(f"Zip: {ARTIFACT_ZIP} ({ARTIFACT_ZIP.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
