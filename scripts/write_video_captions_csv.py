#!/usr/bin/env python3
"""Write a captions CSV mapped 1:1 to the 30s catalog MP4 filenames.

Each episode is exactly one CSV row. copy_caption is description + handle +
hashtags on a single line so a spreadsheet cell copies in one click.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

HANDLE = "@FactsOrWhacks"
PACK_SIZE = 50
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")
ROOT = Path(__file__).resolve().parents[1]


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


def one_line(*chunks: str) -> str:
    words: list[str] = []
    for chunk in chunks:
        words.extend(str(chunk).split())
    return " ".join(words)


MAX_HASHTAGS = 5
BANNED_TAGS = {
    "didyouknow",
    "factsorwhacks",
    "onthisday",
    "fyp",
    "foryou",
    "foryoupage",
    "viral",
    "trending",
    "reels",
    "shorts",
    "tiktok",
    "instagram",
    "youtube",
    "youtubeshorts",
    "historymatters",
    "historyfacts",
    "weirdhistory",
}


def is_banned_hashtag(tag: str) -> bool:
    key = tag.lstrip("#").lower()
    if not key:
        return True
    if key.endswith("tok"):
        return True
    return key in BANNED_TAGS


def title_fallback(title: str) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for word in re.split(r"[^A-Za-z0-9]+", title or ""):
        if len(word) < 4 or is_banned_hashtag(word):
            continue
        tag = f"#{word}"
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        tags.append(tag)
        if len(tags) >= MAX_HASHTAGS:
            break
    return tags


def hashtag_list(raw: str, fallback: str = "") -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for token in (raw or "").split():
        tag = token.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        if is_banned_hashtag(tag):
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        tags.append(tag)
        if len(tags) >= MAX_HASHTAGS:
            break
    if not tags:
        tags = title_fallback(fallback)
    return tags


def glue_sentences(*chunks: str) -> str:
    parts = [one_line(c) for c in chunks if one_line(c)]
    if not parts:
        return ""
    out = parts[0]
    for part in parts[1:]:
        if out[-1] not in ".!?…":
            out += "."
        out += f" {part}"
    return out


def description(title: str, year: str, hook: str, bullets: list[str]) -> str:
    headline = f"{title} ({year})" if year else title
    facts = [b.strip() for b in bullets if str(b).strip()][:2]
    return glue_sentences(headline, hook, *facts)


def copy_caption(desc: str, tags: list[str]) -> str:
    return one_line(desc, HANDLE, " ".join(tags))


def catalog_row(ep: dict, count: int) -> dict[str, str]:
    n = int(ep["n"])
    title = str(ep.get("title") or "").strip()
    hook = str(ep.get("hook") or "").strip()
    bullets = [str(b).strip() for b in (ep.get("bullets") or []) if str(b).strip()]
    year = extract_year(title, hook, *bullets)
    stem = video_stem(n, title)
    tags = hashtag_list(str(ep.get("tags") or ""), fallback=title)
    desc = description(title, year, hook, bullets)
    caption = copy_caption(desc, tags)
    return {
        "video_filename": f"{stem}.mp4",
        "copy_caption": caption,
        "hashtags": " ".join(tags),
        "description": desc,
        "episode_number": str(n),
        "episode_code": f"{n:03d}",
        "path_inside_zip": f"facts-or-whacks-videos/{stem}.mp4",
        "video_zip_pack": pack_name(n, count),
        "artifact_zip": artifact_pack_name(n, count),
        "still_filename": f"{stem}.webp",
        "title": title,
        "year": year,
        "handle": HANDLE,
        "duration_sec": "30",
        "image_credit": str(ep.get("credit") or "").strip(),
    }


def extra_row(
    *,
    n: int,
    title: str,
    year: str,
    filename: str,
    caption_path: Path,
    credit: str,
) -> dict[str, str]:
    raw = caption_path.read_text(encoding="utf-8")
    tags = hashtag_list(
        " ".join(tok for tok in raw.split() if tok.startswith("#")),
        fallback=title,
    )
    caption = one_line(raw)
    skip = {HANDLE.lower(), *(tag.lower() for tag in tags)}
    desc = " ".join(word for word in caption.split() if word.lower() not in skip)
    stem = Path(filename).stem
    return {
        "video_filename": filename,
        "copy_caption": caption,
        "hashtags": " ".join(tags),
        "description": desc,
        "episode_number": str(n),
        "episode_code": f"{n:03d}",
        "path_inside_zip": f"extra/{filename}",
        "video_zip_pack": "",
        "artifact_zip": "",
        "still_filename": f"{stem}.png",
        "title": title,
        "year": year,
        "handle": HANDLE,
        "duration_sec": "30",
        "image_credit": credit,
    }


def extra_rows() -> list[dict[str, str]]:
    catalog = ROOT / "public" / "catalog"
    return [
        extra_row(
            n=396,
            title="Dolly Parton",
            year="1973",
            filename="396-dolly-parton.mp4",
            caption_path=catalog / "dolly-parton-post.txt",
            credit="Photo: Curtis Hilbun, 2010 · CC BY 3.0",
        ),
        extra_row(
            n=397,
            title="Tim Curry",
            year="1946–2026",
            filename="397-tim-curry.mp4",
            caption_path=catalog / "tim-curry-post.txt",
            credit="Photo: Kevin Paul, 2025 · CC BY 4.0",
        ),
        extra_row(
            n=398,
            title="Peter Cullen",
            year="1941–2026",
            filename="398-peter-cullen.mp4",
            caption_path=catalog / "peter-cullen-post.txt",
            credit="Photo: Pedro Heshike, 2023 · CC BY 2.0",
        ),
        extra_row(
            n=399,
            title="Hayden Panettiere",
            year="1989–2026",
            filename="399-hayden-panettiere.mp4",
            caption_path=catalog / "hayden-panettiere-post.txt",
            credit="Photo: Tabercil, 2011 · CC BY-SA 2.0",
        ),
        extra_row(
            n=400,
            title="BTK",
            year="1974–2005",
            filename="400-btk.mp4",
            caption_path=catalog / "btk-post.txt",
            credit="Photo: U.S. Air Force, 1966 · Public domain",
        ),
        extra_row(
            n=401,
            title="Hurricane Katrina",
            year="2005",
            filename="401-hurricane-katrina.mp4",
            caption_path=catalog / "hurricane-katrina-post.txt",
            credit="Photo: Kyle Niemi / U.S. Coast Guard, 2005 · Public domain",
        ),
        extra_row(
            n=402,
            title="Thurgood Marshall",
            year="1967",
            filename="402-thurgood-marshall.mp4",
            caption_path=catalog / "thurgood-marshall-post.txt",
            credit="Photo: Yoichi Okamoto, 1967 · Public domain",
        ),
        extra_row(
            n=403,
            title="Princess Diana",
            year="1961–1997",
            filename="403-princess-diana.mp4",
            caption_path=catalog / "princess-diana-post.txt",
            credit="Photo: White House, 1985 · Public domain",
        ),
        extra_row(
            n=404,
            title="Tupac",
            year="1971–1996",
            filename="404-tupac.mp4",
            caption_path=catalog / "tupac-post.txt",
            credit="Photo: U.S. Department of State, 1995 · Public domain",
        ),
    ]


def rows_from_episodes(episodes: list[dict]) -> list[dict[str, str]]:
    count = len(episodes)
    return [catalog_row(ep, count) for ep in episodes] + extra_rows()


FIELDNAMES = [
    "video_filename",
    "copy_caption",
    "hashtags",
    "description",
    "episode_number",
    "episode_code",
    "path_inside_zip",
    "video_zip_pack",
    "artifact_zip",
    "still_filename",
    "title",
    "year",
    "handle",
    "duration_sec",
    "image_credit",
]


def assert_one_line_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        for key, value in row.items():
            if "\n" in value or "\r" in value:
                raise SystemExit(
                    f"newline in {key} for episode {row.get('episode_number')}"
                )


def write_rows(dest: Path, rows: list[dict[str, str]]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    assert_one_line_rows(rows)
    with dest.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_csv(episodes: list[dict], dest: Path) -> None:
    write_rows(dest, rows_from_episodes(episodes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episodes",
        type=Path,
        default=ROOT / "public/catalog/episodes.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "public/catalog/facts-or-whacks-videos-captions.csv",
    )
    args = parser.parse_args()
    episodes = json.loads(args.episodes.read_text(encoding="utf-8"))
    if len(episodes) != 395:
        raise SystemExit(f"expected 395 episodes, got {len(episodes)}")
    write_csv(episodes, args.out)
    default_out = ROOT / "public/catalog/facts-or-whacks-videos-captions.csv"
    if args.out.resolve() == default_out.resolve():
        extras = extra_rows()
        by_n = {int(row["episode_number"]): row for row in extras}
        write_rows(ROOT / "public/catalog/dolly-parton-post.csv", [by_n[396]])
        write_rows(ROOT / "public/catalog/tim-curry-post.csv", [by_n[397]])
        write_rows(ROOT / "public/catalog/peter-cullen-post.csv", [by_n[398]])
        write_rows(ROOT / "public/catalog/hayden-panettiere-post.csv", [by_n[399]])
        write_rows(ROOT / "public/catalog/btk-post.csv", [by_n[400]])
        write_rows(ROOT / "public/catalog/hurricane-katrina-post.csv", [by_n[401]])
        write_rows(ROOT / "public/catalog/thurgood-marshall-post.csv", [by_n[402]])
        write_rows(ROOT / "public/catalog/princess-diana-post.csv", [by_n[403]])
        write_rows(ROOT / "public/catalog/tupac-post.csv", [by_n[404]])
    print(args.out, args.out.stat().st_size)


if __name__ == "__main__":
    main()
