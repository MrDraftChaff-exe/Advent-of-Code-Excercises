"""Comparable-sales research and list-price recommendations."""

from __future__ import annotations

import json
import random
import re
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

from .specs import product_dir

# Approximate US KDP B&W paperback print cost (large trim like 8.5x11).
# Confirm in KDP before publishing — Amazon updates this.
PRINT_COST = {
    "letter": {"fixed": 0.85, "per_page": 0.012},
    "square": {"fixed": 0.85, "per_page": 0.012},
    "large_square": {"fixed": 0.85, "per_page": 0.012},
    "trade": {"fixed": 0.85, "per_page": 0.012},
    "a5ish": {"fixed": 0.85, "per_page": 0.012},
}

# Fallback market bands when live Amazon fetch is blocked / empty.
NICHE_BANDS = {
    "coloring-book": {"low": 6.99, "mid": 9.99, "high": 12.99, "label": "adult/kids coloring paperbacks"},
    "planner": {"low": 7.99, "mid": 11.99, "high": 16.99, "label": "undated planners"},
    "journal": {"low": 6.99, "mid": 9.99, "high": 14.99, "label": "prompt / lined journals"},
    "logbook": {"low": 6.99, "mid": 8.99, "high": 12.99, "label": "specialty logbooks"},
    "puzzle": {"low": 5.99, "mid": 8.99, "high": 12.99, "label": "puzzle / activity books"},
    "workbook": {"low": 5.99, "mid": 8.99, "high": 11.99, "label": "kids workbooks"},
}


def estimate_print_cost(page_count: int, trim: str = "letter") -> float:
    cfg = PRINT_COST.get(trim, PRINT_COST["letter"])
    return round(cfg["fixed"] + page_count * cfg["per_page"], 2)


def royalty_50(list_price: float, print_cost: float) -> float:
    """KDP 50% royalty marketplace estimate (expanded distribution differs)."""
    return round(max(0.0, list_price * 0.5 - print_cost), 2)


def round_price_point(value: float) -> float:
    """Snap to common Amazon .99 endings."""
    if value < 2.99:
        return 2.99
    whole = int(value)
    return float(f"{whole}.99")


def _parse_amazon_prices(html: str) -> list[dict[str, Any]]:
    """Best-effort parse of public Amazon search HTML (structure changes often)."""
    comps: list[dict[str, Any]] = []
    # Price fragments like $9.99 near titles — keep conservative.
    price_re = re.compile(r"\$([0-9]{1,3}\.[0-9]{2})")
    # data-asin blocks
    for block in re.finditer(
        r'data-asin="([A-Z0-9]{10})"[^>]*>(.{0,2500}?)(?=data-asin="|$)',
        html,
        re.I | re.S,
    ):
        asin, chunk = block.group(1), block.group(2)
        if asin == "0000000000":
            continue
        prices = [float(p) for p in price_re.findall(chunk)]
        prices = [p for p in prices if 2.99 <= p <= 49.99]
        if not prices:
            continue
        title_m = re.search(r'a-text-normal"[^>]*>([^<]{8,160})', chunk)
        title = unescape(title_m.group(1)).strip() if title_m else f"ASIN {asin}"
        title = re.sub(r"\s+", " ", title)
        comps.append(
            {
                "asin": asin,
                "title": title[:120],
                "price_usd": prices[0],
                "url": f"https://www.amazon.com/dp/{asin}",
                "source": "amazon_search",
            }
        )
        if len(comps) >= 20:
            break
    return comps


def fetch_amazon_comps(query: str, limit: int = 12) -> dict[str, Any]:
    """Fetch comparable titles from Amazon search. May fail if Amazon blocks bots."""
    q = urllib.parse.quote_plus(query)
    url = f"https://www.amazon.com/s?k={q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        comps = _parse_amazon_prices(html)[:limit]
        return {
            "ok": bool(comps),
            "query": query,
            "url": url,
            "comps": comps,
            "error": None if comps else "No prices parsed (Amazon HTML may be blocked or changed)",
        }
    except Exception as exc:  # noqa: BLE001 — surface fetch failures to caller
        return {"ok": False, "query": query, "url": url, "comps": [], "error": str(exc)}


def seed_demo_comps(query: str, product_type: str = "coloring-book") -> list[dict[str, Any]]:
    """Deterministic demo comps when live fetch is unavailable (for local preview/dev)."""
    band = NICHE_BANDS.get(product_type, NICHE_BANDS["coloring-book"])
    rng = random.Random(hash(query) & 0xFFFFFFFF)
    titles = [
        f"Bold Patterns — Easy {query.title()} Coloring",
        f"Relaxing Line Art for Adults ({query.title()})",
        f"Simple Geometric Pages to Color",
        f"Mindful Shapes Coloring Book",
        f"Easy Mandala Moments",
        f"Cozy Abstract Coloring for Stress Relief",
        f"Large Print Pattern Coloring",
        f"Calm Pages: {query.title()} Edition",
    ]
    comps = []
    for i, title in enumerate(titles):
        price = round_price_point(rng.uniform(band["low"], band["high"]))
        comps.append(
            {
                "asin": f"DEMO{i:06d}XX",
                "title": title,
                "price_usd": price,
                "url": None,
                "source": "demo_seed",
            }
        )
    return comps


def recommend_price(
    comps: list[dict[str, Any]],
    *,
    page_count: int,
    trim: str,
    product_type: str,
    strategy: str = "median",
) -> dict[str, Any]:
    prices = sorted(float(c["price_usd"]) for c in comps if c.get("price_usd"))
    band = NICHE_BANDS.get(product_type, NICHE_BANDS["coloring-book"])
    if not prices:
        target = band["mid"]
        basis = "niche_band_mid"
    elif strategy == "undercut":
        target = max(band["low"], statistics.median(prices) - 1.0)
        basis = "median_minus_1"
    elif strategy == "premium":
        target = statistics.quantiles(prices, n=4)[-1] if len(prices) >= 4 else max(prices)
        basis = "upper_quartile"
    else:
        target = statistics.median(prices)
        basis = "median"

    list_price = round_price_point(target)
    print_cost = estimate_print_cost(page_count, trim)
    # Ensure roughly $2+ royalty at 50% plan when possible
    min_viable = round_price_point(print_cost * 2 + 2.0)
    if list_price < min_viable:
        list_price = min_viable
        basis += "+raised_for_royalty"

    return {
        "list_price_usd": list_price,
        "strategy": strategy,
        "basis": basis,
        "comp_count": len(prices),
        "comp_min": min(prices) if prices else None,
        "comp_median": round(statistics.median(prices), 2) if prices else None,
        "comp_max": max(prices) if prices else None,
        "print_cost_estimate_usd": print_cost,
        "royalty_50_estimate_usd": royalty_50(list_price, print_cost),
        "niche_band": band,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def load_comps_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "comps" in data:
        data = data["comps"]
    comps = []
    for row in data:
        comps.append(
            {
                "asin": row.get("asin") or row.get("id") or "MANUAL",
                "title": row.get("title") or "Manual comp",
                "price_usd": float(row["price_usd"]),
                "url": row.get("url"),
                "source": row.get("source") or "manual_import",
            }
        )
    return comps


def research_and_price(
    slug: str,
    *,
    query: str | None = None,
    strategy: str = "median",
    allow_demo: bool = True,
    apply: bool = False,
    comps_file: str | Path | None = None,
) -> dict[str, Any]:
    root = product_dir(slug)
    meta_path = root / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    product_type = meta.get("type", "coloring-book")
    keywords = meta.get("keywords") or []
    query = query or " ".join(keywords[:3]) or f"{meta.get('title')} coloring book"

    live = {"ok": False, "error": None, "url": None, "comps": []}
    comps: list[dict[str, Any]] = []
    source = None

    if comps_file:
        comps = load_comps_file(Path(comps_file))
        source = "manual_import"
    else:
        live = fetch_amazon_comps(query)
        comps = list(live.get("comps") or [])
        source = "amazon_search" if comps else None
        if not comps and allow_demo:
            comps = seed_demo_comps(query, product_type)
            source = "demo_seed"

    page_count = int(meta.get("page_count_interior") or (int(meta.get("designs", 30)) * 2) or 60)
    trim = meta.get("trim", "letter")
    recommendation = recommend_price(
        comps,
        page_count=page_count,
        trim=trim,
        product_type=product_type,
        strategy=strategy,
    )

    payload = {
        "slug": slug,
        "query": query,
        "fetch": {"ok": live.get("ok"), "error": live.get("error"), "url": live.get("url")},
        "source": source,
        "comps": comps,
        "recommendation": recommendation,
    }

    out = root / "pricing.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if apply:
        meta["list_price_usd"] = recommendation["list_price_usd"]
        meta["pricing_source"] = source
        meta["pricing_basis"] = recommendation["basis"]
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        payload["applied"] = True
    else:
        payload["applied"] = False

    return payload
