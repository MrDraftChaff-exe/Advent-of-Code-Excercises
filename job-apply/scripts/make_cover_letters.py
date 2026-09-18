#!/usr/bin/env python3
"""Generate short cover-letter drafts for curated target roles."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "cover_letters"
CURATED = ROOT / "data" / "curated_jobs.json"

HEADER = """Montanna Marsh
Reynoldsburg, OH 43068
(380) 237-2454 | montannamarsh@gmail.com

{date}

Hiring Team
{company}

Re: {title}
"""

BODY_PATIENT = """Dear Hiring Team,

I am applying for the {title} role at {company}. With nearly two years as a Collections Tech at the American Red Cross and additional customer service and assistant-manager experience, I am comfortable supporting patients/members, documenting accurately, and staying calm in busy settings.

I am seeking a full-time position near Reynoldsburg, OH (43068) or remote, and I am available for flexible shifts including evenings and weekends when needed. I would welcome the chance to bring reliable communication, attention to detail, and a service-first approach to your team.

Thank you for your consideration.

Sincerely,
Montanna Marsh
"""

BODY_REMOTE_CSR = """Dear Hiring Team,

I am applying for the {title} position at {company}. My background includes high-volume customer service, accurate data entry, and clear phone/in-person communication from roles at the American Red Cross, Sheetz, and as an Assistant Manager.

I live in Ohio and am looking for full-time remote customer care work at $18+/hour. I am dependable, coachable, and experienced working nights, weekends, and holidays when schedules require it.

Thank you for your time and consideration.

Sincerely,
Montanna Marsh
"""

BODY_COLLECTIONS = """Dear Hiring Team,

I am excited to apply for the {title} role at {company}. I previously supported blood collection operations as a Collections Tech with the American Red Cross in Columbus, including sample handling, safety protocol adherence, documentation, and donor communication.

I am seeking full-time work near the Reynoldsburg/Gahanna/Columbus area at $18+/hour and would value the opportunity to continue contributing in a donor-centered environment.

Thank you for considering my application.

Sincerely,
Montanna Marsh
"""


def pick_template(title: str, remote: bool) -> str:
    t = title.lower()
    if "phlebotom" in t or "donor" in t or "collection" in t:
        return BODY_COLLECTIONS
    if remote or "customer service" in t or "insurance" in t:
        return BODY_REMOTE_CSR
    return BODY_PATIENT


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = json.loads(CURATED.read_text()).get("jobs", [])
    date = "September 18, 2026"
    for job in jobs:
        template = pick_template(job["title"], bool(job.get("remote")))
        text = HEADER.format(date=date, company=job["company"], title=job["title"])
        text += "\n" + template.format(title=job["title"], company=job["company"])
        slug = (
            f"{job['company'].split('(')[0].strip().replace(' ', '_')}_"
            f"{job['title'].split('—')[0].strip().replace(' ', '_')}"
        )
        slug = "".join(ch for ch in slug if ch.isalnum() or ch in "_-")[:80]
        path = OUT / f"{slug}.txt"
        path.write_text(text)
        print("wrote", path.name)


if __name__ == "__main__":
    main()
