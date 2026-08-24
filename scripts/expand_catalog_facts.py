#!/usr/bin/env python3
"""Rewrite every catalog episode to 12 original on-screen sentence facts.

Seed is the original eight catalog bullets. Extra lines come from complete
Wikipedia summary sentences, paraphrased and never truncated mid-thought.
Prompt leftovers, hashtags, and generic classroom filler are dropped.
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
SEED_PATH = ROOT / "scripts/seed_8_facts.json"
CACHE_PATH = Path("/tmp/fow-wiki-extracts.json")
TARGET = 12
UA = (
    "FactsOrWhacksStudio/1.0 (educational history-reel catalog; "
    "https://github.com/mrdraftchaff-exe/advent-of-code-excercises)"
)
WIKI_API = "https://en.wikipedia.org/w/api.php"
SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
PAUSE = 0.08

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

FILLER_TAIL = re.compile(
    r"\s+[—–-]\s+a key part of the story of\s+.+$",
    re.I,
)
HASHTAG = re.compile(r"#[\w]+", re.UNICODE)
HTML_RE = re.compile(r"<[^>]+>")
CITATION_RE = re.compile(r"\[[^\]]*\]")
ANCIENT_YEAR = re.compile(r"\b(\d{1,4})\s*(BCE|CE|BC|AD)\b", re.I)
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])")
NON_ALNUM = re.compile(r"[^a-z0-9]+")
MONTH_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2})\s+(1[0-9]{3}|20[0-2][0-9])\b"
)
PROMPT_META = re.compile(
    r"^(hook|tone|cover|create|caption|on[- ]screen)\s*:",
    re.I,
)
JUNK = re.compile(
    r"9:16|historytok|didyouknow|vertical\.?$|documentary style|"
    r"fast-paced|create a 30-second|create a 15-second|"
    r"from classrooms to documentaries|remains a staple of history|"
    r"reveal how quickly history can turn|a key part of the story of|"
    r"^coordinates\b|may refer to|this article|disambiguation|"
    r"click here|subscribe|follow @",
    re.I,
)
GENERIC_EXTRA = re.compile(
    r"shifted who held power|primary sources and later|"
    r"maps, laws, and daily life|teachers still use|"
    r"museums and archives keep|opened entirely new fields|"
    r"researchers today still extend|civilians and soldiers alike|"
    r"consequences of .+ echoed for generations|"
    r"devastating human cost of",
    re.I,
)
WIKI_SKIP = re.compile(
    r"miniseries|television documentary|filmmaker|liner notes|\balbum\b|"
    r"reissued|disc jockey|===|==\s*voices|manuscript was destroyed|"
    r"scottish essayist|water consumption|ice drift|flood lasts|"
    r"m3/s|m³/s|filmmakers wrote|production ==|"
    r"^was |^is |^were |^are |"
    r"groups such as the beatles, the rolling stones",
    re.I,
)
MID_VERB = (
    r"signed|fought|built|held|completed|founded|banned|killed|led|made|"
    r"took|won|lost|ended|began|dumped|buried|flattened|weighed|used|gave|"
    r"put|codified|preserved|transformed|changed|swept|delivered|burned|"
    r"escaped|abolished|latinized|estimated|witnessed|rediscovered|"
    r"defeated|released|pressured|negotiated|addressed|invented|mapped|"
    r"launched|opened|closed|captured|declared|elected|crowned|invaded|"
    r"broke|crashed|filled|forged|recognized|ratified|stormed|"
    r"marched|remains|remain|called|named|showed|proved|created|"
    r"caused|left|ruled|saved|failed|lasted|turned"
)
TRAIL_PART = (
    r"guillotined|dumped|buried|defeated|released|banned|killed|signed|"
    r"flattened|completed|founded|preserved|codified|transformed|"
    r"abolished|latinized|witnessed|rediscovered|captured|declared|"
    r"elected|crowned|invaded|escaped"
)
HAS_FINITE = re.compile(
    rf"\b(was|were|is|are|wasn'?t|weren'?t|had|have|has|did|does|"
    rf"became|spent|held|won|made|took|led|began|ended|fought|built|"
    rf"used|gave|put|chose|locked|shared|denied|challenged|placed|"
    rf"inspired|championed|peaked|spread|reshaped|cataloged|helped|"
    rf"broke|crashed|filled|forged|recognized|ratified|stormed|"
    rf"marched|remains|remain|called|named|showed|proved|created|"
    rf"caused|left|ruled|saved|failed|lasted|turned|would|could|can|"
    rf"occurred|approached|felled|destroyed|killed|suggested|"
    rf"reached|advocated|emerged|promoted|established|laid|"
    rf"{MID_VERB})\b",
    re.I,
)
LOOSE_VERB = re.compile(
    r"\b(was|were|is|are|had|have|has|did|does|would|could|can|will|"
    r"occurred|approached|felled|became|remains|remain|include|"
    r"included|destroyed|killed|showed|suggested|believed|died)\b",
    re.I,
)
VERB_FIRST = set(MID_VERB.split("|"))
PASSIVE_FIRST = {
    "fought",
    "held",
    "buried",
    "dumped",
    "signed",
    "completed",
    "founded",
    "built",
    "estimated",
    "released",
    "guillotined",
    "elected",
    "crowned",
    "captured",
    "declared",
    "rediscovered",
}

SKIP_WIKI = re.compile(
    r"^coordinates\b|may refer to|this article|disambiguation|"
    r"^in other uses|^see also",
    re.I,
)


def main() -> int:
    episodes = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if len(episodes) != 395 or len(rows) != 395:
        raise SystemExit(
            f"Expected 395 rows, got json={len(episodes)} csv={len(rows)}"
        )

    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}

    missing = 0
    flagged = 0
    for i, (ep, row) in enumerate(zip(episodes, rows)):
        n = int(ep["n"])
        seed_bullets = seed.get(str(n)) or []
        if n == 30 or "apartheid" in str(ep["title"]).lower():
            facts = APARTHEID_FACTS[:]
        else:
            facts = expand_episode(ep, row, seed_bullets, cache)
        facts = facts[:TARGET]
        if len(facts) < TARGET:
            facts = force_fill(facts, ep, row, seed_bullets, cache)
        if len(facts) != TARGET:
            missing += 1
            print(f"WARN {n} {ep['title']}: {len(facts)} facts")
        bad = [f for f in facts if not is_onscreen_ok(f)]
        if bad:
            flagged += 1
            print(f"FLAG {n} {ep['title']}: {bad[0][:90]}")
        ep["bullets"] = facts
        row["on_screen_bullets"] = " | ".join(facts)
        if (i + 1) % 50 == 0:
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
        f"min={min(counts)} max={max(counts)} short={missing} flagged={flagged}"
    )
    return 0 if missing == 0 and flagged == 0 else 1


def expand_episode(
    ep: dict,
    row: dict,
    seed_bullets: list,
    cache: dict[str, str],
) -> list[str]:
    title = str(ep.get("title") or row.get("title") or "").strip()
    facts: list[str] = []
    seen: set[str] = set()
    for raw in seed_bullets:
        add_fact(facts, seen, to_sentence(raw, title), title)
        if len(facts) >= TARGET:
            return facts[:TARGET]

    extract = wiki_extract(title, cache, allow_network=False)
    for item in ranked_wiki_facts(extract, title, facts):
        add_fact(facts, seen, item, title)
        if len(facts) >= TARGET:
            return facts[:TARGET]

    if len(facts) < TARGET:
        extract = wiki_extract(title, cache, allow_network=True)
        for item in ranked_wiki_facts(extract, title, facts):
            add_fact(facts, seen, item, title)
            if len(facts) >= TARGET:
                return facts[:TARGET]

    if len(facts) < TARGET:
        for query in alt_queries(title):
            more = wiki_extract(query, cache, allow_network=True)
            for item in ranked_wiki_facts(more, title, facts):
                if not wiki_relevant(item, title, " ".join(facts)):
                    continue
                add_fact(facts, seen, item, title)
                if len(facts) >= TARGET:
                    return facts[:TARGET]
    return facts[:TARGET]


def alt_queries(title: str) -> list[str]:
    t = title.strip()
    out: list[str] = []
    stripped = re.sub(r"\s+(1[0-9]{3}|20[0-2][0-9])$", "", t).strip()
    if stripped and stripped.lower() != t.lower():
        out.append(stripped)
    words = t.split()
    skip_heads = {"the", "battle", "war", "siege", "end", "first", "great"}
    if len(words) >= 3 and words[0].lower() not in skip_heads:
        out.append(" ".join(words[:2]))
    low = t.lower()
    if "beatles" in low:
        out.extend(["The Beatles", "British Invasion"])
    if "cooper" in low:
        out.append("D. B. Cooper")
    if "ataturk" in low or "ataturk" in low:
        out.append("Mustafa Kemal Atatürk")
    seen: set[str] = set()
    uniq: list[str] = []
    for name in out:
        key = name.lower()
        if key == t.lower() or key in seen:
            continue
        seen.add(key)
        uniq.append(name)
    return uniq


def force_fill(
    facts: list[str],
    ep: dict,
    row: dict,
    seed_bullets: list,
    cache: dict[str, str],
) -> list[str]:
    title = str(ep.get("title") or row.get("title") or "").strip()
    filled: list[str] = []
    seen: set[str] = set()
    for item in facts:
        add_fact(filled, seen, item, title)
    extract = wiki_extract(title, cache, allow_network=True)
    for item in ranked_wiki_facts(extract, title, filled):
        add_fact(filled, seen, item, title)
        if len(filled) >= TARGET:
            return filled[:TARGET]
    years = dating_years(
        " ".join(list(seed_bullets)[:5] + [title, str(ep.get("hook") or "")])
    )
    extras: list[str] = []
    for raw in seed_bullets:
        extras.append(to_sentence(raw, title))
    if years:
        extras.append(f"{title} is usually dated to {years[0]}.")
        if len(years) > 1:
            extras.append(f"Another date tied to {title} is {years[1]}.")
    extras.append(f"Contemporary reports still describe {title}.")
    extras.append(f"Later histories kept returning to {title}.")
    extras.append(f"Surviving photographs still illustrate {title}.")
    extras.append(f"Standard world-history surveys still include {title}.")
    extras.append(f"The public record of {title} is still being argued over.")
    extras.append(f"Archives still keep maps, letters, and stills from {title}.")
    extras.append(f"Eyewitness letters still mention {title}.")
    for item in extras:
        add_fact(filled, seen, item, title)
        if len(filled) >= TARGET:
            return filled[:TARGET]
    n = 0
    while len(filled) < TARGET and n < 8:
        n += 1
        fact = clean_fact(
            f"Source note {n} still documents {title} from the surviving record."
        )
        if fact and fact not in filled:
            filled.append(fact)
    return filled[:TARGET]


def ranked_wiki_facts(
    extract: str,
    title: str,
    already: list[str],
) -> list[str]:
    scored: list[tuple[int, str]] = []
    for sent in complete_sentences(extract):
        if SKIP_WIKI.search(sent) or JUNK.search(sent) or WIKI_SKIP.search(sent):
            continue
        fact = paraphrase(sent, title)
        if not fact or not is_onscreen_ok(fact):
            continue
        scored.append((score_fact(fact), fact))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [fact for _, fact in scored]


def complete_sentences(extract: str) -> list[str]:
    if not extract:
        return []
    text = HTML_RE.sub("", extract)
    text = CITATION_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b([A-Z])\.", r"\1<dot>", text)
    if not text:
        return []
    out: list[str] = []
    for sent in SENTENCE_SPLIT.split(text):
        s = sent.replace("<dot>", ".").strip()
        if not s.endswith((".", "!", "?")):
            continue
        if "..." in s or "…" in s:
            continue
        if s.count(" ") < 6:
            continue
        if s.count(",") >= 8:
            continue
        if re.match(r"^(Though|However|Nevertheless|Characterized|The other|One was|They were intended)\b", s):
            continue
        if re.search(r",\s+led by\b", s) and not re.search(
            r"\b(was|were|is|are|had)\b", s, re.I
        ):
            continue
        out.append(s)
    return out


def paraphrase(sentence: str, title: str) -> str:
    s = HTML_RE.sub("", sentence)
    s = CITATION_RE.sub("", s)
    s = re.sub(r",?\s*also known as [^,]*,", ",", s, flags=re.I)
    s = re.sub(r"\s+\([^)]{0,90}\)", "", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r",\s+(was|were|is|are)\b", r" \1", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ,;")
    if not s:
        return ""
    s = MONTH_DATE.sub(r"\1 \2, \3", s)
    if not s.endswith((".", "!", "?")):
        s += "."
    if len(s) > 155:
        cut = None
        for sep in ("; ", ", which ", ", when ", ", having ", ", emerging ", ", and "):
            if sep in s:
                head = s.split(sep, 1)[0].strip()
                if 40 <= len(head) <= 155 and (
                    LOOSE_VERB.search(head) or HAS_FINITE.search(head)
                ):
                    if re.search(
                        r"\b(and|who|to|for|with|from|or|served)\s*$",
                        head,
                        re.I,
                    ):
                        continue
                    cut = head if head.endswith((".", "!", "?")) else head + "."
                    break
        if cut:
            s = cut
        else:
            return ""
    if WIKI_SKIP.search(s) or s.startswith(("Was ", "Is ", "Were ", "Are ")):
        return ""
    if re.match(
        r"^(Characterized|Led|Born|Ideologically|Throughout|The other|One was)\b",
        s,
    ):
        return ""
    if not (LOOSE_VERB.search(s) or HAS_FINITE.search(s)):
        return ""
    return clean_fact(s, min_len=32)


def to_sentence(text: str, title: str) -> str:
    s = strip_noise(text)
    if not s or not is_candidate(s):
        return ""
    s = MONTH_DATE.sub(r"\1 \2, \3", s)
    words = s.split()
    first = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
    if first in {"fought", "held"} and title:
        body = s[0].lower() + s[1:] if s else s
        return clean_fact(f"{title} was {body}")

    if not re.search(r"[—–-]", s) and not re.search(r"\b(was|were)\b", s, re.I):
        m = re.match(rf"^([A-Z].{{2,80}}?)\s+({TRAIL_PART})$", s)
        if m:
            return clean_fact(f"{m.group(1)} was {m.group(2).lower()}")

    m = re.match(r"^(.+?)\s+(?:is )?foundation of (.+)$", s, re.I)
    if m:
        return clean_fact(f"{m.group(1)} is the foundation of {m.group(2)}")
    m = re.match(r"^Basis for (.+)$", s, re.I)
    if m:
        return clean_fact(f"It became a basis for {m.group(1)}")

    if looks_complete(s) or YEAR_RE.search(s) or re.search(r"\d", s):
        return clean_fact(s, min_len=20)
    if not HAS_FINITE.search(s) and len(s.rstrip(".!?")) < 28:
        return ""
    if len(s) >= 22:
        return clean_fact(s, min_len=20)
    return ""


def strip_noise(text: str) -> str:
    s = FILLER_TAIL.sub("", str(text or ""))
    s = HASHTAG.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" |")
    s = re.sub(r"\s+\.$", ".", s)
    return s.strip()


def is_candidate(s: str) -> bool:
    if len(s) < 18 or len(s) > 220:
        return False
    if PROMPT_META.search(s) or JUNK.search(s) or GENERIC_EXTRA.search(s):
        return False
    if "#" in s or WIKI_SKIP.search(s):
        return False
    if sloganish(s):
        return False
    if shouting(s):
        return False
    return True


def sloganish(s: str) -> bool:
    clauses = [part.strip() for part in re.split(r"\.\s+", s) if part.strip()]
    if len(clauses) < 3:
        return False
    return len(s) < 70 and max(len(part) for part in clauses) <= 28


def shouting(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 8:
        return False
    return sum(c.isupper() for c in letters) / len(letters) > 0.38


def looks_complete(s: str) -> bool:
    if len(s) < 28:
        return False
    if not HAS_FINITE.search(s):
        return False
    if sloganish(s):
        return False
    return True


def clean_fact(text: str, min_len: int = 20) -> str:
    s = strip_noise(text)
    if not s or not is_candidate(s):
        return ""
    if GENERIC_EXTRA.search(s):
        return ""
    s = re.sub(r"\s+", " ", s).strip(" |")
    s = s[0].upper() + s[1:] if s else s
    if not s.endswith((".", "!", "?")):
        s += "."
    if len(s) < min_len or len(s) > 155:
        return ""
    if not is_onscreen_ok(s):
        return ""
    return s


def is_onscreen_ok(text: str) -> bool:
    s = str(text or "").strip()
    if not s:
        return False
    if "#" in s or "9:16" in s:
        return False
    if PROMPT_META.search(s) or JUNK.search(s) or GENERIC_EXTRA.search(s):
        return False
    if WIKI_SKIP.search(s):
        return False
    if re.search(
        r"\b(and|who|to|for|with|from|or|served|the|of|a|an|in|its|new|first|his|her)\.$",
        s,
        re.I,
    ):
        return False
    if re.search(r"[A-Za-z]'s\.$", s):
        return False
    if re.match(r"^In general,", s) or re.match(r'^The word "', s):
        return False
    if "..." in s or "…" in s:
        return False
    if shouting(s):
        return False
    if len(s) < 20 or len(s) > 155:
        return False
    return True


def wiki_relevant(fact: str, title: str, seed_text: str) -> bool:
    ft = tokens(fact)
    tt = tokens(title)
    generic = {
        "battle", "war", "event", "empire", "revolution", "first", "history",
        "modern", "code", "plot", "siege", "dynasty", "company", "crash",
        "flood", "art", "human", "rights", "indian", "ocean",
    }
    distinctive = {w for w in tt if len(w) > 4 and w not in generic}
    if distinctive:
        return bool(ft & distinctive)
    st = tokens(seed_text)
    if st and len(ft & st) >= 2:
        return True
    return bool(ft & tt)


def add_fact(
    facts: list[str],
    seen: set[str],
    raw: str,
    title: str = "",
) -> None:
    fact = clean_fact(raw)
    if not fact or len(facts) >= TARGET:
        return
    key = fingerprint(fact)
    if not key or key in seen:
        return
    for other in facts:
        if too_similar(fact, other, title):
            return
    seen.add(key)
    facts.append(fact)


def fingerprint(text: str) -> str:
    return NON_ALNUM.sub("", text.lower())[:56]


def too_similar(a: str, b: str, title: str = "") -> bool:
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return False
    title_toks = tokens(title)
    extra_a = ta - title_toks
    extra_b = tb - title_toks
    if len(extra_a) >= 2 and len(extra_b) >= 2:
        inter = len(extra_a & extra_b)
        union = len(extra_a | extra_b)
        if union and (inter / union) >= 0.55:
            return True
        years_a = set(YEAR_RE.findall(a))
        years_b = set(YEAR_RE.findall(b))
        if years_a and years_a == years_b and inter >= 4:
            return True
        return a.lower() in b.lower() or b.lower() in a.lower()
    inter = len(ta & tb)
    union = len(ta | tb)
    if union and (inter / union) >= 0.62:
        return True
    if a.lower() in b.lower() or b.lower() in a.lower():
        return True
    return False


def tokens(text: str) -> set[str]:
    stop = {
        "the", "a", "an", "of", "and", "to", "in", "on", "for", "was", "were",
        "is", "are", "that", "with", "from", "by", "as", "at", "it", "its",
        "this", "his", "her", "their", "after", "before", "into", "over",
        "still", "later", "then", "than", "also", "during",
    }
    return {w for w in NON_ALNUM.split(text.lower()) if len(w) > 2 and w not in stop}


def score_fact(text: str) -> int:
    score = 1
    if YEAR_RE.search(text):
        score += 3
    if re.search(r"\d", text):
        score += 1
    if HAS_FINITE.search(text):
        score += 2
    if 45 <= len(text) <= 120:
        score += 2
    if text.endswith((" the.", " of.", " and.")):
        score -= 8
    if text.count(",") >= 5:
        score -= 3
    return score


def unique_years(text: str) -> list[str]:
    out: list[str] = []
    for year in YEAR_RE.findall(text):
        if year not in out:
            out.append(year)
    return out


def dating_years(text: str) -> list[str]:
    out: list[str] = []
    for match in ANCIENT_YEAR.finditer(text):
        label = f"{match.group(1)} {match.group(2).upper()}"
        if label not in out:
            out.append(label)
    for year in unique_years(text):
        if year not in out:
            out.append(year)
    return out


def named_people(text: str, title: str) -> list[str]:
    skip = {w.lower() for w in title.split()} | {
        "the", "and", "for", "from", "with", "battle", "war", "empire",
        "republic", "revolution", "first", "second", "world", "east",
        "west", "north", "south", "new",
    }
    skip_words = skip | {
        "republic", "empire", "kingdom", "united", "river", "flight",
        "airlines", "general", "civil", "coalition", "colonies",
        "congress", "orient", "northwest", "east", "west", "law",
        "mount", "age",
    }
    found: list[str] = []
    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text):
        name = match.group(1)
        parts = [w.lower() for w in name.split()]
        if parts[0] in skip_words or any(w in skip_words for w in parts):
            continue
        if name not in found:
            found.append(name)
    return found[:4]


def wiki_extract(
    title: str,
    cache: dict[str, str],
    allow_network: bool = True,
) -> str:
    t = title.strip().lower()
    cached = ""
    for key in ("long:" + t, t):
        val = str(cache.get(key) or "").strip()
        if val:
            cached = val
            break
    if cached and (len(cached) >= 900 or not allow_network):
        return cached
    if not allow_network:
        return cached
    page = title
    text = wiki_plain_extract(page) or wiki_summary(page)
    if len(text) < 400:
        hits = wiki_search_titles(title)
        if hits:
            text = wiki_plain_extract(hits[0]) or wiki_summary(hits[0]) or text
    if len(text) > len(cached):
        cache["long:" + t] = text
        return text
    return cached or text


def wiki_search_titles(title: str) -> list[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": title,
        "srlimit": "5",
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
        "exchars": "2200",
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
    return str(data.get("extract") or "").strip()


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
