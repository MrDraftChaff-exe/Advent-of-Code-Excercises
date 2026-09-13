#!/usr/bin/env python3
"""Fetch Google Trends (US) and classify queries for the daily reel pick.

This does not pick the extra by itself. It is the first filter in DAILY_REEL.md:
Trends that can be a 12-fact PD/CC extra beat newsjack and on-this-day.

Skip sports scores, gadget launches, licensed games, celebrity gossip, and
crypto memes. Hold a Trends anniversary that is not today (9/11 on Sep 10).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

RSS_URL = "https://trends.google.com/trending/rss?geo=US"
UA = "FactsOrWhacks/1.0 (daily topic pick; +https://github.com)"

# MM-DD hooks that explode on the calendar day, not the eve.
HOLD_ANNIVERSARIES: dict[tuple[int, int], tuple[str, ...]] = {
    (9, 11): (
        "9/11",
        "9-11",
        "september 11 2001",
        "september 11, 2001",
        "sept. 11, 2001",
        "world trade center",
        "flight 93",
    ),
}

SKIP_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "licensed game",
        (
            "fortnite",
            "wolverine",
            "playstation",
            "xbox",
            "epic games",
            "steam ",
            "ps5",
            "video game",
            "marvel's wolverine",
        ),
    ),
    (
        "sports score",
        (
            "football",
            "baseball",
            "nba ",
            "nfl ",
            "ncaa",
            "mlb ",
            "nhl ",
            "touchdown",
            "quarterback",
            "western michigan",
            "uefa",
            "champions league",
            "betting tips",
        ),
    ),
    (
        "product launch",
        (
            "iphone",
            "foldable",
            "apple unveils",
            "android phone",
            "gadget",
        ),
    ),
    (
        "celebrity gossip",
        (
            "cheating",
            "ex-husband",
            "skipped",
            "funeral",
            "husband",
            "late partner",
            "opens up about",
        ),
    ),
    (
        "crypto meme",
        ("meme coin", "crypto coin", "cryptosphere"),
    ),
    (
        "current entertainment booking",
        ("saturday night live", "snl ", "katseye"),
    ),
)

HISTORY_HINTS = (
    "anniversary",
    "years ago",
    "died",
    "death",
    "war",
    "verdict",
    "trial",
    "confirmation",
    "invent",
    "first ",
    "history",
    "remember",
    "witness",
)


def local_tag(tag: str) -> str:
    return tag.split("}")[-1]


def child_text(el: ET.Element, name: str) -> str:
    for child in list(el):
        if local_tag(child.tag) == name:
            return (child.text or "").strip()
    return ""


def children(el: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(el) if local_tag(child.tag) == name]


def parse_rss(xml: str) -> list[dict[str, object]]:
    root = ET.fromstring(xml)
    items: list[dict[str, object]] = []
    channel = root.find("channel")
    if channel is None:
        return items
    for item in children(channel, "item"):
        news = [
            child_text(node, "news_item_title")
            for node in children(item, "news_item")
        ]
        news = [title for title in news if title]
        items.append(
            {
                "title": child_text(item, "title"),
                "traffic": child_text(item, "approx_traffic"),
                "news": news,
            }
        )
    return items


def blob_of(item: dict[str, object]) -> str:
    news = item.get("news") or []
    parts = [str(item.get("title") or "")]
    parts.extend(str(n) for n in news)
    return " ".join(parts).lower()


def anniversary_day(blob: str) -> tuple[int, int] | None:
    for day, keys in HOLD_ANNIVERSARIES.items():
        if any(key in blob for key in keys):
            return day
    return None


def has_needle(blob: str, needle: str) -> bool:
    if " " in needle or needle.endswith(" "):
        return needle in blob
    return re.search(rf"\b{re.escape(needle)}\b", blob) is not None


def historical_year(blob: str, today: date) -> bool:
    for match in re.finditer(r"\b(1[0-9]{3}|20[0-2][0-9])\b", blob):
        if int(match.group(1)) <= today.year - 5:
            return True
    return False


def classify(item: dict[str, object], today: date) -> dict[str, str]:
    blob = blob_of(item)
    for reason, needles in SKIP_RULES:
        if any(has_needle(blob, needle) for needle in needles):
            return {"status": "skip", "reason": reason}
    hold = anniversary_day(blob)
    if hold and (today.month, today.day) != hold:
        return {
            "status": "hold",
            "reason": f"anniversary is {hold[0]:02d}-{hold[1]:02d}",
        }
    if hold:
        return {"status": "candidate", "reason": "anniversary is in Trends today"}
    if historical_year(blob, today) or any(has_needle(blob, hint) for hint in HISTORY_HINTS):
        return {"status": "candidate", "reason": "history-shaped search"}
    return {"status": "weak", "reason": "no still-and-12-facts hook yet"}


def fetch_rss(url: str = RSS_URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_today(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="US")
    parser.add_argument("--date", help="YYYY-MM-DD used for hold-until-anniversary")
    parser.add_argument("--fixture", type=Path, help="Local RSS XML instead of network")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    today = parse_today(args.date)
    if args.fixture:
        xml = args.fixture.read_text(encoding="utf-8")
    else:
        url = RSS_URL if args.geo == "US" else f"{RSS_URL.split('?')[0]}?geo={args.geo}"
        try:
            xml = fetch_rss(url)
        except OSError as exc:
            print(f"trends fetch failed: {exc}", file=sys.stderr)
            return 1
    rows = []
    for item in parse_rss(xml):
        verdict = classify(item, today)
        rows.append({**item, **verdict})
    if args.json:
        json.dump({"date": today.isoformat(), "items": rows}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"Google Trends US  {today.isoformat()}")
    print("status    traffic   query")
    for row in rows:
        title = str(row["title"])
        print(
            f"{row['status']:<9} {str(row['traffic']):<9} {title}"
            f"  ({row['reason']})"
        )
    print()
    print(
        "Pick a candidate if it can be 12 short facts and a PD/CC still. "
        "Hold means wait for the anniversary. Skip the rest. "
        "If nothing fits, use newsjack, then on-this-day."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
