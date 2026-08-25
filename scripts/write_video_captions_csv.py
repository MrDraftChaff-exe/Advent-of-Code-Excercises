#!/usr/bin/env python3
"""Write a captions CSV mapped 1:1 to the 30s catalog MP4 filenames."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

HANDLE = "@FactsOrWhacks"
PACK_SIZE = 50
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    slug = slug.strip("-")[:48]
    return slug or "facts-or-whacks"


def video_stem(n: int, title: str) -> str:
    return slugify(f"{n:03d}-{title}")


def pack_name(n: int, count: int = 395, size: int = PACK_SIZE) -> str:
    start = ((n - 1) // size) * size + 1
    end = min(start + size - 1, count)
    return f"facts-or-whacks-videos-{start:03d}-{end:03d}.zip"


def artifact_pack_name(n: int, count: int = 395, size: int = PACK_SIZE) -> str:
    start = ((n - 1) // size) * size + 1
    end = min(start + size - 1, count)
    return f"videos_30s_pack_{start:03d}_{end:03d}.zip"


def extract_year(*chunks: str) -> str:
    matches = YEAR_RE.findall(" ".join(chunks))
    return matches[-1] if matches else ""


def hashtag_list(raw: str) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for token in (raw or "").split():
        tag = token.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        tags.append(tag)
    brand = "#FactsOrWhacks"
    if brand.lower() not in seen:
        tags.append(brand)
    return tags


def description(title: str, year: str, hook: str, bullets: list[str]) -> str:
    headline = f"{title} ({year})" if year else title
    facts = [b.strip() for b in bullets if str(b).strip()][:2]
    parts = [headline]
    if hook.strip():
        parts.append(hook.strip())
    if facts:
        parts.append("")
        parts.extend(facts)
    return "\n".join(parts).strip()


def paste_caption(desc: str, tags: list[str]) -> str:
    return "\n".join([desc, "", HANDLE, " ".join(tags)]).strip()


def rows_from_episodes(episodes: list[dict]) -> list[dict[str, str]]:
    count = len(episodes)
    out: list[dict[str, str]] = []
    for ep in episodes:
        n = int(ep["n"])
        title = str(ep.get("title") or "").strip()
        hook = str(ep.get("hook") or "").strip()
        bullets = [str(b).strip() for b in (ep.get("bullets") or []) if str(b).strip()]
        year = extract_year(title, hook, *bullets)
        stem = video_stem(n, title)
        tags = hashtag_list(str(ep.get("tags") or ""))
        desc = description(title, year, hook, bullets)
        out.append(
            {
                "episode_number": str(n),
                "episode_code": f"{n:03d}",
                "video_filename": f"{stem}.mp4",
                "path_inside_zip": f"facts-or-whacks-videos/{stem}.mp4",
                "video_zip_pack": pack_name(n, count),
                "artifact_zip": artifact_pack_name(n, count),
                "still_filename": f"{stem}.webp",
                "title": title,
                "year": year,
                "description": desc,
                "hashtags": " ".join(tags),
                "paste_caption": paste_caption(desc, tags),
                "handle": HANDLE,
                "duration_sec": "30",
                "image_credit": str(ep.get("credit") or "").strip(),
            }
        )
    return out


FIELDNAMES = [
    "episode_number",
    "episode_code",
    "video_filename",
    "path_inside_zip",
    "video_zip_pack",
    "artifact_zip",
    "still_filename",
    "title",
    "year",
    "description",
    "hashtags",
    "paste_caption",
    "handle",
    "duration_sec",
    "image_credit",
]


def write_csv(episodes: list[dict], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = rows_from_episodes(episodes)
    with dest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episodes",
        type=Path,
        default=Path("public/catalog/episodes.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("public/catalog/facts-or-whacks-videos-captions.csv"),
    )
    args = parser.parse_args()
    episodes = json.loads(args.episodes.read_text(encoding="utf-8"))
    if len(episodes) != 395:
        raise SystemExit(f"expected 395 episodes, got {len(episodes)}")
    write_csv(episodes, args.out)
    print(args.out, args.out.stat().st_size)


if __name__ == "__main__":
    main()
