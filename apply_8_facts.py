#!/usr/bin/env python3
"""Apply 8 facts from facts_395x8.json to facts-or-whacks-395-videos.csv and export txt zip."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

JSON_PATH = Path("/workspace/facts_395x8.json")
CSV_PATH = Path("/workspace/facts-or-whacks-395-videos.csv")
EXPORT_SCRIPT = Path("/workspace/export_txt_zip.py")


def load_facts() -> dict[int, dict]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_num = {}
    for entry in data:
        num = int(entry["topic_number"])
        facts = entry["facts"]
        if len(facts) != 8:
            raise ValueError(f"Topic {num} has {len(facts)} facts, expected 8")
        by_num[num] = entry
    return by_num


def update_video_prompt(existing: str, title: str, hook: str, facts: list[str]) -> str:
    cover_text = ". ".join(f.rstrip(".") for f in facts) + "."
    if "Cover:" in existing:
        prefix = existing.split("Cover:", 1)[0]
        suffix = ""
        if "Tone:" in existing:
            suffix = " Tone:" + existing.split("Tone:", 1)[1]
        return f"{prefix}Cover: {cover_text}{suffix}"
    return (
        f"Create a 30-second vertical history short about {title}. "
        f"Hook: {hook} Cover: {cover_text} "
        f"Tone: dramatic, fast-paced, documentary style. 9:16 vertical."
    )


def main() -> None:
    facts_by_num = load_facts()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if len(rows) != 395:
        raise SystemExit(f"Expected 395 CSV rows, got {len(rows)}")

    for row in rows:
        num = int(row["topic_number"])
        entry = facts_by_num.get(num)
        if not entry:
            raise SystemExit(f"Missing facts for topic {num}")
        if row["title"] != entry["title"]:
            raise SystemExit(
                f"Title mismatch topic {num}: CSV={row['title']!r} JSON={entry['title']!r}"
            )
        facts = entry["facts"]
        row["on_screen_bullets"] = " | ".join(facts)
        row["video_prompt"] = update_video_prompt(
            row["video_prompt"], row["title"], row["hook"], facts
        )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {len(rows)} rows in {CSV_PATH}")

    result = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT)],
        check=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)


if __name__ == "__main__":
    main()
