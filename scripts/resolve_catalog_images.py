#!/usr/bin/env python3
"""Download a real Wikimedia Commons still for every catalog episode.

Guessed upload.wikimedia.org URLs 404. This script searches Wikipedia,
Wikidata P18, then Commons, saves a raster thumb locally, and rewrites
the catalog to those paths. Resume-safe.

  python3 scripts/resolve_catalog_images.py
  python3 scripts/resolve_catalog_images.py --start 1 --end 10
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public/catalog/facts-or-whacks-395.csv"
JSON_PATH = ROOT / "public/catalog/episodes.json"
OUT_DIR = ROOT / "public/images/catalog"
MANIFEST_PATH = OUT_DIR / "manifest.json"
ATTR_PATH = OUT_DIR / "ATTRIBUTION.md"

UA = (
    "FactsOrWhacksStudio/1.0 (https://github.com/mrdraftchaff-exe/advent-of-code-excercises; "
    "educational history-reel catalog; fetching freely licensed Commons stills)"
)
WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

THUMB_WIDTH = 1280
MIN_BYTES = 8000
MIN_EDGE = 360
REQUEST_GAP = 0.16
MAX_TRIES = 6

RASTER_MIMES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
SKIP_RE = re.compile(
    r"screenshot|\.pdf$|favicon|placeholder|no[_\s-]?image|wikidata-logo|"
    r"commons-logo|padlock|icon[-_]|fileicon|202[3-9]",
    re.I,
)
HTML_RE = re.compile(r"<[^>]+>")
SLUG_RE = re.compile(r"[^a-z0-9]+")
BAD_WD = (
    "disambiguation",
    "scientific article",
    "video game",
    "wikimedia category",
    "episode of",
)

_last_request = 0.0


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    episodes = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if len(episodes) != 395:
        raise SystemExit(f"Expected 395 JSON episodes, got {len(episodes)}")

    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    csv_by_n = {int(r["topic_number"]): r for r in rows if r.get("topic_number")}
    manifest = load_manifest()
    failed: list[dict] = []
    done = 0

    numbers = (
        [int(x) for x in args.only.split(",") if x.strip()]
        if args.only
        else list(range(args.start, args.end + 1))
    )
    for n in numbers:
        ep = next((item for item in episodes if int(item["n"]) == n), None)
        if not ep:
            failed.append({"n": n, "reason": "missing from JSON"})
            continue
        row = csv_by_n.get(n)
        try:
            hit = None if args.force else find_existing(n, ep, manifest)
            if hit is None:
                hit = resolve_one(ep, row)
            if hit is None:
                failed.append({"n": n, "title": ep["title"], "reason": "no image"})
                print(f"[{n}/395] FAIL  {ep['title']}", flush=True)
                continue
            apply_hit(ep, row, hit)
            manifest[str(n)] = hit
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            done += 1
            print(
                f"[{n}/395] {ep['title']} -> {Path(hit['file']).name} "
                f"{hit['bytes']}B {hit.get('source_file', '')}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            failed.append({"n": n, "title": ep.get("title"), "reason": str(exc)})
            print(f"[{n}/395] ERROR {ep.get('title')}: {exc}", flush=True)

    for extra in ("image_credit", "image_source"):
        if extra not in fields:
            fields.append(extra)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    JSON_PATH.write_text(json.dumps(episodes, ensure_ascii=False) + "\n", encoding="utf-8")
    write_attribution(episodes, manifest)

    print(f"\nWrote catalog. Succeeded {done}. Failed {len(failed)}.", flush=True)
    if failed:
        print(json.dumps(failed, indent=2), file=sys.stderr)
        return 1
    if not args.only and args.start == 1 and args.end == 395:
        bad = [ep["n"] for ep in episodes if not str(ep.get("image", "")).startswith("/images/catalog/")]
        if bad:
            print(f"Non-local images remain: {bad[:20]}", file=sys.stderr)
            return 1
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=395)
    p.add_argument("--force", action="store_true")
    p.add_argument("--only", default="", help="Comma-separated episode numbers")
    return p.parse_args()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def find_existing(n: int, ep: dict, manifest: dict) -> dict | None:
    hit = manifest.get(str(n))
    if hit and magic_path(hit.get("file", "")):
        return hit
    for path in sorted(OUT_DIR.glob(f"{n:03d}-*")):
        if magic_path(path):
            return {
                "n": n,
                "file": str(path),
                "public_path": f"/images/catalog/{path.name}",
                "bytes": path.stat().st_size,
                "source_file": path.name,
                "commons_page": "",
                "credit": ep.get("credit") or "Wikimedia Commons",
                "license": "",
                "via": "disk",
            }
    image = str(ep.get("image") or "")
    if image.startswith("/images/") and not image.startswith("/images/catalog/"):
        return copy_bundled(ep, image)
    return None


def copy_bundled(ep: dict, public_path: str) -> dict | None:
    src = ROOT / "public" / public_path.lstrip("/")
    if not magic_path(src):
        return None
    ext = magic_path(src)
    dest_name = f"{int(ep['n']):03d}-{slug(ep['title'])}.{ext}"
    dest = OUT_DIR / dest_name
    if src.resolve() != dest.resolve():
        dest.write_bytes(src.read_bytes())
    mandela = "mandela" in src.name.lower()
    return {
        "n": int(ep["n"]),
        "file": str(dest),
        "public_path": f"/images/catalog/{dest_name}",
        "bytes": dest.stat().st_size,
        "source_file": src.name,
        "commons_page": (
            "https://commons.wikimedia.org/wiki/File:Mandela_voting_in_1994.jpg"
            if mandela
            else ""
        ),
        "credit": (
            "Photo: Paul Weinberg, 1994 · CC BY-SA 3.0" if mandela else "Wikimedia Commons"
        ),
        "license": "CC BY-SA 3.0" if mandela else "",
        "via": "local",
    }


def apply_hit(ep: dict, row: dict | None, hit: dict) -> None:
    ep["image"] = hit["public_path"]
    ep["credit"] = hit.get("credit") or "Wikimedia Commons"
    ep["source"] = hit.get("commons_page") or ""
    if row is not None:
        row["image_url"] = hit["public_path"]
        row["image_credit"] = ep["credit"]
        row["image_source"] = ep["source"]


def write_attribution(episodes: list[dict], manifest: dict) -> None:
    lines = [
        "# Catalog stills",
        "",
        "Every episode photograph is a freely licensed Wikimedia Commons file,",
        "downloaded here so the studio never depends on a live upload URL.",
        "",
    ]
    for ep in episodes:
        hit = manifest.get(str(ep["n"]))
        if not hit:
            continue
        lines += [f"## {ep['n']}. {ep['title']}", ""]
        lines.append(f"- Local: `{hit.get('public_path')}`")
        src = hit.get("source_file") or ""
        page = hit.get("commons_page") or ""
        if src and page:
            lines.append(f"- File: [{src}]({page})")
        elif src:
            lines.append(f"- File: `{src}`")
        if hit.get("credit"):
            lines.append(f"- Credit: {hit['credit']}")
        if hit.get("license"):
            lines.append(f"- License: {hit['license']}")
        lines.append("")
    ATTR_PATH.write_text("\n".join(lines), encoding="utf-8")


def resolve_one(ep: dict, row: dict | None) -> dict | None:
    original = ((row or {}).get("image_url") or ep.get("image") or "").strip()
    if original.startswith("/") and not original.startswith("//"):
        copied = copy_bundled(ep, original)
        if copied:
            return copied
    guessed = upload_filename(original)
    if guessed:
        saved = try_save(ep, commons_lookup(guessed))
        if saved:
            return saved
    queries = queries_for(ep)
    if queries:
        saved = try_save(ep, wiki_lead_image(queries[0]))
        if saved:
            return saved
        saved = try_save(ep, wikidata_image(queries[0]))
        if saved:
            return saved
    for query in queries:
        for cand in commons_search_images(query):
            saved = try_save(ep, cand)
            if saved:
                return saved
    for query in queries[1:]:
        saved = try_save(ep, wiki_lead_image(query))
        if saved:
            return saved
        saved = try_save(ep, wikidata_image(query))
        if saved:
            return saved
    return None


def try_save(ep: dict, cand: dict | None) -> dict | None:
    if not cand or not cand.get("download_url"):
        return None
    label = cand.get("title") or cand.get("source_file") or ""
    if SKIP_RE.search(str(label)):
        return None
    width = int(cand.get("width") or 0)
    height = int(cand.get("height") or 0)
    if width and height and max(width, height) < MIN_EDGE:
        return None
    try:
        blob = http_get_bytes(cand["download_url"])
    except Exception as exc:  # noqa: BLE001
        print(f"  download failed {label}: {exc}", flush=True)
        return None
    ext = magic_ext(blob)
    if not ext or len(blob) < MIN_BYTES:
        return None
    dest_name = f"{int(ep['n']):03d}-{slug(ep['title'])}.{ext}"
    dest = OUT_DIR / dest_name
    dest.write_bytes(blob)
    return {
        "n": int(ep["n"]),
        "file": str(dest),
        "public_path": f"/images/catalog/{dest_name}",
        "bytes": len(blob),
        "source_file": drop_file_prefix(str(label)),
        "commons_page": cand.get("commons_page") or file_page_url(str(label)),
        "credit": cand.get("credit") or "Wikimedia Commons",
        "license": cand.get("license") or "",
        "via": cand.get("via") or "commons",
    }


def _tokens(text: str) -> set[str]:
    stop = {
        "the",
        "of",
        "and",
        "a",
        "an",
        "in",
        "on",
        "for",
        "to",
        "by",
        "with",
        "from",
    }
    return {tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if tok not in stop}


def _related(query: str, title: str) -> bool:
    weak = {
        "first",
        "great",
        "best",
        "award",
        "history",
        "modern",
        "world",
        "new",
        "old",
        "war",
        "battle",
        "picture",
        "film",
        "movie",
    }
    q = _tokens(query) - weak
    if not q:
        q = _tokens(query)
    need = 2 if len(q) >= 2 else 1
    return len(q & _tokens(title)) >= need


def wiki_lead_image(query: str) -> dict | None:
    data = mw_get(
        WIKI_API,
        action="query",
        generator="search",
        gsrsearch=query,
        gsrlimit=6,
        gsrnamespace=0,
        prop="pageimages|pageprops",
        piprop="thumbnail|name",
        pithumbsize=THUMB_WIDTH,
        redirects=1,
        maxlag=5,
    )
    pages = sorted(data.get("query", {}).get("pages") or [], key=lambda p: p.get("index", 99))
    q_toks = _tokens(query)
    for page in pages:
        if page.get("pageprops", {}).get("disambiguation") is not None:
            continue
        title = str(page.get("title") or "")
        if "(disambiguation)" in title.lower():
            continue
        if not _related(query, title):
            continue
        thumb = (page.get("thumbnail") or {}).get("source") or ""
        if thumb and "/commons/" not in thumb:
            continue
        filename = page.get("pageimage")
        if not filename:
            continue
        meta = commons_lookup(filename)
        if meta:
            meta["via"] = f"wikipedia:{title}"
            return meta
    return None


def wikidata_image(query: str) -> dict | None:
    search = mw_get(
        WIKIDATA_API,
        action="wbsearchentities",
        search=query,
        language="en",
        uselang="en",
        type="item",
        limit=6,
    )
    for hit in search.get("search") or []:
        desc = str(hit.get("description") or "").lower()
        if any(token in desc for token in BAD_WD):
            continue
        claims = mw_get(
            WIKIDATA_API,
            action="wbgetclaims",
            entity=hit["id"],
            property="P18",
        )
        for claim in claims.get("claims", {}).get("P18") or []:
            if claim.get("rank") == "deprecated":
                continue
            fname = (claim.get("mainsnak") or {}).get("datavalue", {}).get("value")
            if not fname:
                continue
            meta = commons_lookup(fname)
            if meta:
                meta["via"] = f"wikidata:{hit['id']}"
                return meta
    return None


def commons_search_images(query: str) -> list[dict]:
    data = mw_get(
        COMMONS_API,
        action="query",
        generator="search",
        gsrsearch=f"filetype:bitmap {query}",
        gsrnamespace=6,
        gsrlimit=8,
        prop="imageinfo",
        iiprop="url|size|mime|extmetadata",
        iiurlwidth=THUMB_WIDTH,
        maxlag=5,
    )
    cands = []
    for page in data.get("query", {}).get("pages") or []:
        cand = page_to_candidate(page, "commons-search")
        if cand:
            cands.append(cand)
    cands.sort(key=score, reverse=True)
    return cands


def commons_lookup(filename: str) -> dict | None:
    title = filename if str(filename).startswith("File:") else f"File:{filename}"
    data = mw_get(
        COMMONS_API,
        action="query",
        titles=title,
        prop="imageinfo",
        iiprop="url|size|mime|extmetadata",
        iiurlwidth=THUMB_WIDTH,
        maxlag=5,
    )
    pages = data.get("query", {}).get("pages") or []
    if not pages or pages[0].get("missing") or pages[0].get("invalid"):
        return None
    return page_to_candidate(pages[0], "commons-file")


def page_to_candidate(page: dict, via: str) -> dict | None:
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    mime = str(info.get("mime") or "")
    if mime not in RASTER_MIMES:
        return None
    url = drop_query(info.get("thumburl") or info.get("url") or "")
    if "/commons/" not in url:
        return None
    meta = info.get("extmetadata") or {}
    license_name = meta_text(meta, "LicenseShortName")
    artist = html_text(meta_text(meta, "Artist") or meta_text(meta, "Credit"))
    return {
        "title": page.get("title"),
        "source_file": drop_file_prefix(page.get("title") or ""),
        "mime": mime,
        "width": info.get("thumbwidth") or info.get("width") or 0,
        "height": info.get("thumbheight") or info.get("height") or 0,
        "download_url": url,
        "commons_page": file_page_url(page.get("title") or ""),
        "license": license_name,
        "credit": credit_line(artist, license_name),
        "via": via,
    }


def score(cand: dict) -> int:
    n = 0
    mime = cand.get("mime")
    if mime == "image/jpeg":
        n += 4
    elif mime in ("image/png", "image/webp"):
        n += 2
    width = int(cand.get("width") or 0)
    if width >= 800:
        n += 2
    if width >= 1200:
        n += 1
    name = f"{cand.get('title', '')} {cand.get('source_file', '')}"
    if re.search(r"portrait|painting|photograph|photo|battle|map|lithograph", name, re.I):
        n += 2
    if SKIP_RE.search(name):
        n -= 8
    return n


def queries_for(ep: dict) -> list[str]:
    out: list[str] = []

    def add(raw: str) -> None:
        text = re.sub(r"\s+", " ", str(raw or "")).strip()
        if 3 <= len(text) < 90 and text not in out:
            out.append(text)

    title = str(ep.get("title") or "")
    add(title)
    add(re.sub(r"^The\s+", "", title, flags=re.I))
    add(title.replace("'s", ""))
    for part in re.split(r"\s+and\s+|\s+[—–:/-]\s+", title):
        add(part)
    words = re.sub(r"[^\w\s'-]", " ", title).split()
    if len(words) > 3:
        add(" ".join(words[:3]))
    weak = {
        "first",
        "great",
        "war",
        "battle",
        "discovery",
        "invention",
        "crisis",
        "scandal",
        "panic",
        "modern",
        "movement",
        "end",
        "rise",
        "fall",
        "age",
        "era",
    }
    if words and words[0].lower() not in weak:
        add(words[0])
    elif len(words) > 1:
        add(" ".join(words[1:]))
    add(re.split(r"[.!?]", str(ep.get("hook") or ""))[0])
    bullets = ep.get("bullets") or []
    if bullets:
        add(re.split(r"[—–.]", str(bullets[0]))[0])
    return out


def upload_filename(url: str) -> str | None:
    if not url or "upload.wikimedia.org" not in url:
        return None
    try:
        clean = urllib.parse.unquote(url.split("?", 1)[0])
        if "/thumb/" in clean:
            parts = clean.split("/thumb/", 1)[1].split("/")
            if len(parts) >= 3:
                return parts[2]
        name = clean.rstrip("/").split("/")[-1]
        return name or None
    except Exception:
        return None


def file_page_url(title: str) -> str:
    name = drop_file_prefix(title).replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name)


def drop_file_prefix(title: str) -> str:
    return re.sub(r"^File:", "", str(title or ""), flags=re.I)


def credit_line(artist: str, license_name: str) -> str:
    lic = license_name or "Wikimedia Commons"
    if artist:
        return f"{shorten(artist, 72)} · {lic}"
    return f"Wikimedia Commons · {lic}"


def meta_text(meta: dict, key: str) -> str:
    val = (meta.get(key) or {}).get("value")
    return "" if val is None else str(val)


def html_text(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = HTML_RE.sub(" ", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#039;", "'")
        .replace("&nbsp;", " ")
    )
    return re.sub(r"\s+", " ", text).strip()


def shorten(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def drop_query(url: str) -> str:
    return url.split("?", 1)[0]


def slug(title: str) -> str:
    return (SLUG_RE.sub("-", title.lower()).strip("-") or "episode")[:56]


def magic_ext(buf: bytes) -> str | None:
    if len(buf) < 12:
        return None
    if buf[0] == 0xFF and buf[1] == 0xD8 and buf[2] == 0xFF:
        return "jpg"
    if buf[:4] == b"\x89PNG":
        return "png"
    if buf[:3] == b"GIF":
        return "gif"
    if buf[:4] == b"RIFF" and buf[8:12] == b"WEBP":
        return "webp"
    return None


def magic_path(path: Path | str) -> str | None:
    p = Path(path)
    if not p.is_file() or p.stat().st_size < MIN_BYTES:
        return None
    return magic_ext(p.read_bytes()[:32])


def http_get_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/jpeg,image/png,image/webp,image/gif,*/*",
            "Accept-Language": "en",
        },
    )
    pause()
    with urllib.request.urlopen(req, timeout=60) as resp:
        if getattr(resp, "status", 200) >= 400:
            raise RuntimeError(f"HTTP {resp.status}")
        return resp.read()


def mw_get(base: str, **params) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    params["format"] = "json"
    params["formatversion"] = "2"
    url = base + "?" + urllib.parse.urlencode(params)
    last_err: Exception | None = None
    for attempt in range(MAX_TRIES):
        pause()
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Api-User-Agent": UA,
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            err = payload.get("error") if isinstance(payload, dict) else None
            if err:
                code = str(err.get("code") or "")
                if code in {"maxlag", "ratelimited"}:
                    time.sleep(1.2 * (2**attempt))
                    continue
                raise RuntimeError(err)
            return payload
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in {429, 500, 502, 503, 504}:
                time.sleep(0.8 * (2**attempt))
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.4 * (2**attempt))
    raise last_err or RuntimeError(f"Failed {url}")


def pause() -> None:
    global _last_request
    now = time.time()
    wait = REQUEST_GAP - (now - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.time()


if __name__ == "__main__":
    raise SystemExit(main())
