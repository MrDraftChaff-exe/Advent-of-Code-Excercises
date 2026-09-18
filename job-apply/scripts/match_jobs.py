#!/usr/bin/env python3
"""Match remote/public job feeds to Montanna's criteria and write output files."""

from __future__ import annotations

import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

MIN_WAGE = 18.0
HOME_LAT = 39.9551
HOME_LON = -82.8035

PHYSICAL_BLOCK = [
    "warehouse",
    "forklift",
    "construction",
    "laborer",
    "mover",
    "cdl",
    "landscape",
    "roofing",
    "dishwasher",
    "line cook",
    "bartender",
    "cna ",
    "home health aide",
    "caregiver",
    "freight",
    "pallet",
    "heavy lifting",
    "manufacturing associate",
    "production associate",
]

GOOD_KEYWORDS = [
    "customer service",
    "customer support",
    "call center",
    "collections",
    "phlebotom",
    "donor",
    "medical receptionist",
    "front desk",
    "administrative",
    "admin assistant",
    "office assistant",
    "data entry",
    "laboratory",
    "lab assistant",
    "specimen",
    "receptionist",
    "teller",
    "patient service",
    "patient access",
    "scheduler",
    "coordinator",
    "assistant manager",
    "client service",
    "support specialist",
]


def fetch_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "montanna-job-match/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def parse_wage(text: str | None):
    if not text:
        return None
    t = str(text).lower().replace(",", "")
    m = re.search(
        r"\$?\s*(\d{2}(?:\.\d{1,2})?)\s*(?:-|to|/)?\s*(?:\$?\s*(\d{2}(?:\.\d{1,2})?))?\s*(?:/?\s*hr|per\s*hour|hourly)",
        t,
    )
    if m:
        vals = [float(x) for x in m.groups() if x]
        return max(vals) if vals else None
    m = re.search(r"\$(\d{2,3}),?(\d{3})\s*(?:per\s*year|/yr|annually|a year)", t)
    if m:
        return round(float(m.group(1) + m.group(2)) / 2080, 2)
    return None


def is_physical(text: str) -> bool:
    t = text.lower()
    return any(b in t for b in PHYSICAL_BLOCK)


def score_job(title: str, desc: str, *, remote: bool = False, wage=None):
    blob = f"{title} {desc}".lower()
    score = 0
    reasons = []
    hits = [k for k in GOOD_KEYWORDS if k in blob]
    # Require a real skill keyword so senior tech roles do not pollute the queue.
    if not hits:
        return -100, ["no skill keyword match"]
    score += min(40, len(hits) * 8)
    reasons.append("skill-fit: " + ", ".join(hits[:4]))
    if remote:
        score += 20
        reasons.append("remote")
    if wage is not None:
        if wage >= MIN_WAGE:
            score += 20
            reasons.append(f"${wage}+/hr likely")
        else:
            score -= 30
            reasons.append(f"pay below ${MIN_WAGE}")
    else:
        score += 5
        reasons.append("pay not listed — verify $18+")
    if is_physical(blob):
        score -= 50
        reasons.append("physically demanding — filter")
    if "part-time" in blob or "part time" in blob:
        score -= 25
        reasons.append("part-time")
    elif "full-time" in blob or "full time" in blob:
        score += 10
        reasons.append("full-time")
    # Soft-penalize clearly senior/software tracks
    for bad in ("senior software", "devops", "golang", "react full", "ai engineer", "gpu"):
        if bad in blob:
            score -= 40
            reasons.append(f"unlikely fit ({bad})")
    return score, reasons


def collect_remotive(jobs: list):
    urls = [
        "https://remotive.com/api/remote-jobs?category=customer-support",
        "https://remotive.com/api/remote-jobs?search=administrative",
        "https://remotive.com/api/remote-jobs?search=customer%20service",
    ]
    for url in urls:
        try:
            payload = fetch_json(url)
        except Exception as exc:  # noqa: BLE001
            print(f"remotive skip ({url}): {exc}")
            continue
        for item in payload.get("jobs", []):
            title = item.get("title") or ""
            desc = item.get("description") or ""
            wage = parse_wage(desc) or parse_wage(title)
            score, reasons = score_job(title, desc, remote=True, wage=wage)
            if score < 28 or is_physical(f"{title} {desc}"):
                continue
            jobs.append(
                {
                    "id": f"remotive-{item.get('id')}",
                    "title": title,
                    "company": item.get("company_name") or "",
                    "location": "Remote",
                    "remote": True,
                    "url": item.get("url") or "",
                    "source": "Remotive",
                    "wage_guess": wage,
                    "score": score,
                    "reasons": reasons,
                    "snippet": re.sub(r"<[^>]+>", " ", desc)[:280].strip(),
                }
            )


def collect_arbeitnow(jobs: list):
    try:
        for page in range(1, 3):
            payload = fetch_json(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
            for item in payload.get("data", []):
                title = item.get("title") or ""
                desc = item.get("description") or ""
                loc = item.get("location") or ""
                remote = bool(item.get("remote")) or "remote" in loc.lower()
                blob = f"{title} {desc} {loc}".lower()
                if not remote and "ohio" not in blob and "columbus" not in blob:
                    continue
                wage = parse_wage(desc) or parse_wage(title)
                score, reasons = score_job(title, desc, remote=remote, wage=wage)
                if score < 28 or is_physical(blob):
                    continue
                jobs.append(
                    {
                        "id": f"arbeitnow-{abs(hash(item.get('url') or title)) % 10**10}",
                        "title": title,
                        "company": item.get("company_name") or "",
                        "location": loc or ("Remote" if remote else "Unknown"),
                        "remote": remote,
                        "url": item.get("url") or "",
                        "source": "Arbeitnow",
                        "wage_guess": wage,
                        "score": score,
                        "reasons": reasons,
                        "snippet": re.sub(r"<[^>]+>", " ", desc)[:280].strip(),
                    }
                )
    except Exception as exc:  # noqa: BLE001
        print(f"arbeitnow skip: {exc}")


def merge_curated(jobs: list):
    curated_path = DATA / "curated_jobs.json"
    if not curated_path.exists():
        return
    curated = json.loads(curated_path.read_text())
    for item in curated.get("jobs", []):
        jobs.append(
            {
                "id": f"curated-{abs(hash(item['url'])) % 10**10}",
                "title": item["title"],
                "company": item["company"],
                "location": item["location"],
                "remote": bool(item.get("remote")),
                "url": item["url"],
                "source": item.get("source") or "Other",
                "wage_guess": None,
                "score": int(item.get("fit_score") or 0),
                "reasons": [item.get("notes") or "curated local match"],
                "snippet": item.get("notes") or "",
                "stage": item.get("stage") or "Saved",
                "pay": item.get("pay"),
            }
        )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs: list[dict] = []
    collect_remotive(jobs)
    collect_arbeitnow(jobs)
    merge_curated(jobs)

    seen = set()
    unique = []
    for job in sorted(jobs, key=lambda j: -j["score"]):
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "home_zip": "43068",
        "criteria": {
            "min_hourly": MIN_WAGE,
            "full_time": True,
            "radius_minutes": 30,
            "remote_ok": True,
            "avoid_physical": True,
        },
        "jobs": unique,
    }
    out_json = OUT / "matched_jobs.json"
    out_json.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Matched jobs",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "| Score | Title | Company | Location | Pay/Notes | Link |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for job in unique[:40]:
        pay = job.get("pay") or (f"${job['wage_guess']}/hr" if job.get("wage_guess") else "verify")
        lines.append(
            f"| {job['score']} | {job['title'][:60]} | {job['company'][:40]} | "
            f"{job['location'][:30]} | {pay} | [apply]({job['url']}) |"
        )
    out_md = OUT / "matched_jobs.md"
    out_md.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(unique)} jobs -> {out_json} and {out_md}")


if __name__ == "__main__":
    main()
