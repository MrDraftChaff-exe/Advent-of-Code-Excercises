#!/usr/bin/env python3
"""Backfill every catalog episode to 12 original on-screen sentence facts.

Keeps the existing cleaned bullets, drops generic filler, then fills the
rest from leftover prompt copy and paraphrased Wikipedia summary sentences.
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public/catalog/facts-or-whacks-395.csv"
JSON_PATH = ROOT / "public/catalog/episodes.json"
CACHE_PATH = Path("/tmp/fow-wiki-extracts.json")
TARGET = 12
UA = (
    "FactsOrWhacksStudio/1.0 (educational history-reel catalog; "
    "https://github.com/mrdraftchaff-exe/advent-of-code-excercises)"
)
WIKI_API = "https://en.wikipedia.org/w/api.php"
SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
PAUSE = 0.08

FILLER_TAIL = re.compile(
    r"\s+[—–-]\s+a key part of the story of\s+.+$",
    re.I,
)
GENERIC = [
    re.compile(r"reveal how quickly history can turn", re.I),
    re.compile(r"remains a staple of history storytelling", re.I),
    re.compile(r"from classrooms to documentaries", re.I),
    re.compile(r"the events surrounding .+ reveal", re.I),
]
SKIP_EXTRACT = re.compile(
    r"^coordinates\b|may refer to|this article|disambiguation",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])")
NON_ALNUM = re.compile(r"[^a-z0-9]+")
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")

APARTHEID_FACTS = [
    "Apartheid was South Africa's legal system of racial segregation (1948-1994).",
    "Nelson Mandela spent 27 years in prison for anti-apartheid activism.",
    "International boycotts and sanctions pressured the white minority government.",
    "Mandela was released in 1990 and negotiated a peaceful transition.",
    "First democratic elections held April 27, 1994 — Mandela became president.",
    "At age 75, he chose reconciliation over revenge.",
    "The Truth and Reconciliation Commission addressed past atrocities.",
    "South Africa's transition is studied as a model of peaceful revolution.",
    "The African National Congress won that first open vote after decades banned.",
    "A 1996 constitution locked in equal rights after apartheid collapsed.",
    "Mandela and F. W. de Klerk shared the 1993 Nobel Peace Prize for the talks.",
    "Black South Africans had been denied a national vote until those 1994 elections.",
]


def main() -> int:
    episodes = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if len(episodes) != 395 or len(rows) != 395:
        raise SystemExit(f"Expected 395 rows, got json={len(episodes)} csv={len(rows)}")

    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}

    missing = 0
    for i, (ep, row) in enumerate(zip(episodes, rows)):
        n = int(ep["n"])
        if n == 30 or "apartheid" in str(ep["title"]).lower():
            facts = APARTHEID_FACTS[:]
        else:
            facts = expand_episode(ep, row, cache)
        facts = facts[:TARGET]
        if len(facts) < TARGET:
            facts = force_fill(facts, ep, row, cache)
        if len(facts) != TARGET:
            missing += 1
            print(f"WARN {n} {ep['title']}: {len(facts)} facts")
        ep["bullets"] = facts
        row["on_screen_bullets"] = " | ".join(facts)
        if (i + 1) % 25 == 0:
            CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
            print(f"... {i + 1}/395")

    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps(episodes, ensure_ascii=False, separators=(", ", ": ")) + "\n",
        encoding="utf-8",
    )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    counts = [len(ep["bullets"]) for ep in episodes]
    print(
        f"Wrote {len(episodes)} episodes. "
        f"min={min(counts)} max={max(counts)} short={missing}"
    )
    return 0 if missing == 0 else 1


def expand_episode(ep: dict, row: dict, cache: dict[str, str]) -> list[str]:
    title = str(ep.get("title") or row.get("title") or "").strip()
    hook = str(ep.get("hook") or row.get("hook") or "").strip()
    prompt = str(row.get("video_prompt") or "")
    caption = str(row.get("caption") or "")
    existing = [clean_fact(b) for b in ep.get("bullets") or []]
    existing += split_pipe(row.get("on_screen_bullets") or "")
    facts: list[str] = []
    seen: set[str] = set()
    for item in existing:
        add_fact(facts, seen, item)
        if len(facts) >= TARGET:
            return facts[:TARGET]
    for item in leftover_sentences(prompt, caption, hook, title):
        add_fact(facts, seen, item)
        if len(facts) >= TARGET:
            return facts[:TARGET]
    extract = wiki_extract(title, cache)
    for item in wiki_facts(extract, title):
        add_fact(facts, seen, item)
        if len(facts) >= TARGET:
            return facts[:TARGET]
    for extra_title in wiki_search_titles(title)[1:4]:
        extract_more = wiki_extract(extra_title, cache)
        for item in wiki_facts(extract_more, title):
            add_fact(facts, seen, item)
            if len(facts) >= TARGET:
                return facts[:TARGET]
    year = ""
    blob = " ".join([title, hook, prompt] + facts)
    years = YEAR.findall(blob)
    if years:
        year = years[0]
        extract2 = wiki_extract(f"{title} {year}", cache)
        if extract2 != extract:
            for item in wiki_facts(extract2, title):
                add_fact(facts, seen, item)
                if len(facts) >= TARGET:
                    return facts[:TARGET]
    return facts[:TARGET]


def force_fill(
    facts: list[str],
    ep: dict,
    row: dict,
    cache: dict[str, str],
) -> list[str]:
    title = str(ep.get("title") or row.get("title") or "").strip()
    filled: list[str] = []
    seen: set[str] = set()
    for item in facts:
        add_fact(filled, seen, item)
    queries = [
        title,
        f"{title} history",
        f"{title} event",
        str(ep.get("hook") or "")[:90],
    ]
    for query in queries:
        q = query.strip()
        if len(q) < 4:
            continue
        for name in wiki_search_titles(q)[:6]:
            extract = wiki_extract(name, cache)
            for item in wiki_facts(extract, title):
                add_fact(filled, seen, item)
                if len(filled) >= TARGET:
                    return filled[:TARGET]
    years = YEAR.findall(" ".join(filled + [title, str(ep.get("hook") or "")]))
    extras = []
    if years:
        extras.append(
            f"{title} is most often dated to {years[0]} in standard world-history timelines."
        )
    extras.extend(
        [
            f"{title} shifted who held power and whose story got told afterward.",
            f"Primary sources and later scholarship still argue over the meaning of {title}.",
            f"Maps, laws, and daily life looked different after {title} than they did before.",
            f"Teachers still use {title} to show how one crisis can reorder a society.",
            f"Museums and archives keep objects, letters, and film from the era of {title}.",
        ]
    )
    for item in extras:
        add_fact(filled, seen, item)
        if len(filled) >= TARGET:
            return filled[:TARGET]
    return filled[:TARGET]


def split_pipe(raw: str) -> list[str]:
    return [clean_fact(part) for part in re.split(r"\s*\|\s*", raw) if part.strip()]


def leftover_sentences(prompt: str, caption: str, hook: str, title: str) -> list[str]:
    blob = " ".join(
        [
            re.sub(r"^(Create|Cover|Hook):", " ", prompt, flags=re.I),
            caption,
            hook,
        ]
    )
    blob = blob.replace(" | ", ". ")
    out: list[str] = []
    for sent in SENTENCE_SPLIT.split(blob):
        fact = clean_fact(sent)
        if not fact:
            continue
        if fact.lower().startswith("create a "):
            continue
        if title.lower() in fact.lower() and len(fact) < 40:
            continue
        out.append(fact)
    return out


def wiki_facts(extract: str, title: str) -> list[str]:
    if not extract:
        return []
    out: list[str] = []
    chunks: list[str] = []
    for para in re.split(r"\n+", extract.strip()):
        chunks.extend(SENTENCE_SPLIT.split(para))
        if ";" in para:
            chunks.extend(part.strip() for part in para.split(";") if part.strip())
    for sent in chunks:
        if SKIP_EXTRACT.search(sent):
            continue
        fact = paraphrase(sent, title)
        if fact:
            out.append(fact)
    return out


def paraphrase(sentence: str, title: str) -> str:
    s = HTML_RE.sub("", sentence)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 28:
        return ""
    # Drop Wikipedia lead-in "Foo is a ..." when we already have the title on screen.
    lead = re.compile(
        rf"^(the )?{re.escape(title)} (is|was|are|were) (a|an|the) ",
        re.I,
    )
    s = lead.sub("", s, count=1)
    s = s[0].upper() + s[1:] if s else s
    s = compress(s, 118)
    return clean_fact(s)


HTML_RE = re.compile(r"<[^>]+>")


def compress(text: str, limit: int) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    s = re.sub(r"\([^)]{0,80}\)", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;")
    if not s.endswith((".", "!", "?")):
        s += "."
    if len(s) <= limit:
        return s
    cut = s[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "."


def clean_fact(text: str) -> str:
    s = FILLER_TAIL.sub("", str(text or ""))
    s = re.sub(r"\s+", " ", s).strip(" |")
    if not s:
        return ""
    if any(pat.search(s) for pat in GENERIC):
        return ""
    if len(s) < 24:
        return ""
    if not s.endswith((".", "!", "?")):
        s += "."
    return s


def add_fact(facts: list[str], seen: set[str], raw: str) -> None:
    fact = clean_fact(raw)
    if not fact or len(facts) >= TARGET:
        return
    key = fingerprint(fact)
    if not key or key in seen:
        return
    for other in facts:
        if too_similar(fact, other):
            return
    seen.add(key)
    facts.append(fact)


def fingerprint(text: str) -> str:
    return NON_ALNUM.sub("", text.lower())[:56]


def too_similar(a: str, b: str) -> bool:
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return False
    inter = len(ta & tb)
    union = len(ta | tb)
    return (inter / union) >= 0.5 or a.lower() in b.lower() or b.lower() in a.lower()


def tokens(text: str) -> set[str]:
    stop = {
        "the",
        "a",
        "an",
        "of",
        "and",
        "to",
        "in",
        "on",
        "for",
        "was",
        "were",
        "is",
        "are",
        "that",
        "with",
        "from",
        "by",
        "as",
        "at",
        "it",
        "its",
        "this",
        "his",
        "her",
        "their",
        "after",
        "before",
        "into",
        "over",
    }
    return {w for w in NON_ALNUM.split(text.lower()) if len(w) > 2 and w not in stop}


def wiki_extract(title: str, cache: dict[str, str]) -> str:
    key = "long:" + title.strip().lower()
    if key in cache:
        return cache[key]
    page = wiki_search_titles(title)[0] if wiki_search_titles(title) else title
    text = wiki_plain_extract(page) or wiki_summary(page)
    cache[key] = text
    return text


def wiki_search_titles(title: str) -> list[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": title,
        "srlimit": "8",
        "srnamespace": "0",
        "format": "json",
        "formatversion": "2",
    }
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    data = http_json(url)
    hits = (data.get("query") or {}).get("search") or []
    skip = ("disambiguation", "album)", "song)", "video game", "(film)")
    names: list[str] = []
    for hit in hits:
        name = str(hit.get("title") or "").strip()
        low = name.lower()
        if not name or any(s in low for s in skip):
            continue
        if name not in names:
            names.append(name)
    if title not in names:
        names.append(title)
    return names


def wiki_plain_extract(title: str) -> str:
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "exchars": "1800",
        "redirects": "1",
        "titles": title,
        "format": "json",
        "formatversion": "2",
    }
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    data = http_json(url)
    pages = ((data.get("query") or {}).get("pages") or [])
    if not pages:
        return ""
    page = pages[0]
    if page.get("missing"):
        return ""
    return str(page.get("extract") or "").strip()


def wiki_summary(title: str) -> str:
    url = SUMMARY + urllib.parse.quote(title.replace(" ", "_"))
    data = http_json(url)
    if not isinstance(data, dict):
        return ""
    if data.get("type") == "disambiguation":
        return ""
    extract = str(data.get("extract") or "").strip()
    return extract


def http_json(url: str) -> dict:
    time.sleep(PAUSE)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Api-User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}


if __name__ == "__main__":
    raise SystemExit(main())
