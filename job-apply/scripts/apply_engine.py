#!/usr/bin/env python3
"""One-click apply automations for curated postings."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output" / "apply_logs"
RESUME_CANDIDATES = [
    ROOT / "resume" / "Montanna_Marsh_Enhanced_Resume.docx",
    Path("/home/ubuntu/.cursor/projects/workspace/uploads/Montanna_Marsh_Sunbury_Vet_Clinic_Resume_2030.docx"),
]


@dataclass
class ApplyResult:
    job_id: str
    company: str
    title: str
    url: str
    status: str  # submitted | filled_needs_captcha | filled_needs_review | blocked | error | skipped
    message: str
    screenshot: str | None = None
    at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d["at"]:
            d["at"] = datetime.now(timezone.utc).isoformat()
        return d


def load_candidate() -> dict:
    path = DATA / "candidate.local.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    return json.loads(path.read_text())


def load_jobs() -> list[dict]:
    curated = json.loads((DATA / "curated_jobs.json").read_text())["jobs"]
    for i, job in enumerate(curated):
        job.setdefault("id", f"job-{i}")
        job.setdefault("stage", "Saved")
    # merge runtime stage overrides
    state_path = DATA / "apply_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        by_url = {j["url"]: j for j in state.get("jobs", [])}
        for job in curated:
            if job["url"] in by_url:
                job["stage"] = by_url[job["url"]].get("stage", job["stage"])
                job["last_apply"] = by_url[job["url"]].get("last_apply")
    return curated


def save_job_stage(url: str, stage: str, last_apply: dict | None = None) -> None:
    state_path = DATA / "apply_state.json"
    state = {"jobs": []}
    if state_path.exists():
        state = json.loads(state_path.read_text())
    found = False
    for job in state["jobs"]:
        if job.get("url") == url:
            job["stage"] = stage
            if last_apply:
                job["last_apply"] = last_apply
            found = True
            break
    if not found:
        entry = {"url": url, "stage": stage}
        if last_apply:
            entry["last_apply"] = last_apply
        state["jobs"].append(entry)
    state_path.write_text(json.dumps(state, indent=2))


def resume_path(candidate: dict) -> Path:
    configured = Path(candidate.get("resume_path") or "")
    if not configured.is_absolute():
        configured = Path("/workspace") / configured
    for path in [configured, *RESUME_CANDIDATES]:
        if path and Path(path).exists():
            return Path(path)
    raise FileNotFoundError("Enhanced resume DOCX not found")


def platform_for(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "lever.co" in host:
        return "lever"
    if "myworkdayjobs.com" in host or "workday" in host:
        return "workday"
    if "linkedin.com" in host:
        return "linkedin"
    if "indeed.com" in host:
        return "indeed"
    if "remotive.com" in host:
        return "remotive"
    return "generic"


def _fill(page: Page, selector: str, value: str) -> None:
    loc = page.locator(selector)
    if loc.count() == 0:
        return
    loc.first.click()
    loc.first.fill("")
    loc.first.fill(value)


def _select_contains(page: Page, name: str, wanted: str) -> bool:
    sel = page.locator(f'select[name="{name}"]')
    if sel.count() == 0:
        return False
    options = sel.first.evaluate(
        "e => [...e.options].map(o => ({v:o.value, t:o.textContent.trim()}))"
    )
    wanted_l = wanted.lower().strip()
    # Prefer exact match, then startswith, then contains.
    ranked = []
    for opt in options:
        text = (opt["t"] or "").lower().strip()
        val = (opt["v"] or "").lower().strip()
        if not opt["v"]:
            continue
        if text == wanted_l or val == wanted_l:
            ranked.append((0, opt["v"]))
        elif text.startswith(wanted_l) or val.startswith(wanted_l):
            ranked.append((1, opt["v"]))
        elif wanted_l in text or wanted_l in val:
            ranked.append((2, opt["v"]))
    if ranked:
        ranked.sort(key=lambda x: x[0])
        sel.first.select_option(ranked[0][1])
        return True
    return False


def apply_lever(page: Page, job: dict, candidate: dict, resume: Path, submit: bool) -> ApplyResult:
    job_id = job.get("id") or job["url"]
    apply_url = job["url"].rstrip("/")
    if not apply_url.endswith("/apply"):
        apply_url = apply_url + "/apply"

    page.goto(apply_url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector('input[name="name"]', timeout=45000)
    page.wait_for_timeout(800)

    # Cookie banners
    for label in ("Accept", "accept", "Agree"):
        btn = page.get_by_role("button", name=re.compile(label, re.I))
        if btn.count():
            try:
                btn.first.click(timeout=1000)
            except Exception:
                pass

    page.set_input_files("#resume-upload-input", str(resume))
    # Lever parses the resume and can overwrite fields — wait, then force-fill.
    for _ in range(30):
        analyzing = page.locator("text=/Analyzing resume/i").count()
        if analyzing == 0:
            break
        page.wait_for_timeout(500)
    page.wait_for_timeout(800)

    def fill_all_fields() -> None:
        _fill(page, 'input[name="name"]', candidate["full_name"])
        _fill(page, 'input[name="email"]', candidate["email"])
        _fill(page, 'input[name="phone"]', candidate.get("phone_display") or candidate["phone"])
        if candidate.get("location_search"):
            _fill(page, "#location-input", candidate["location_search"])
            page.wait_for_timeout(700)
            suggestion = page.locator(
                ".dropdown-container .dropdown-list li, .location-list li, [role=option]"
            )
            if suggestion.count():
                suggestion.first.click()
        if candidate.get("current_company"):
            _fill(page, 'input[name="org"]', candidate["current_company"])

        _select_contains(page, "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field0]", "External")
        street_local = (candidate.get("street") or "").strip()
        if street_local:
            _fill(
                page,
                'input[name="cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field1]"]',
                street_local,
            )
        _fill(
            page,
            'input[name="cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field2]"]',
            candidate.get("city_state_zip_country")
            or "Reynoldsburg, OH 43068, United States",
        )
        _select_contains(
            page,
            "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field3]",
            candidate.get("hear_about") or "LinkedIn",
        )
        _select_contains(
            page,
            "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field5]",
            candidate.get("education") or "HS Diploma",
        )
        _select_contains(
            page,
            "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field6]",
            "No I haven't worked",
        )
        # Exact "No" for visa question — avoid matching longer Yes option text first.
        _select_contains(page, "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field7]", "No")
        _fill(
            page,
            'input[name="cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field8]"]',
            candidate.get("desired_hourly") or "19",
        )
        _select_contains(page, "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field9]", "Hybrid")
        _select_contains(page, "cards[b59f5ad7-9eb3-49b4-b45d-db844fc7b5c7][field10]", "Yes")

        _select_contains(page, "cards[a22d54a4-6c3f-489f-a5f1-3adffc1dabf3][field0]", "Yes")
        _select_contains(page, "cards[a22d54a4-6c3f-489f-a5f1-3adffc1dabf3][field1]", "Yes")
        _select_contains(page, "cards[a22d54a4-6c3f-489f-a5f1-3adffc1dabf3][field2]", "Yes")
        _select_contains(page, "cards[a22d54a4-6c3f-489f-a5f1-3adffc1dabf3][field3]", "Yes")

        _select_contains(page, "eeo[gender]", candidate.get("eeo_gender") or "Decline")
        _select_contains(page, "eeo[race]", candidate.get("eeo_race") or "Decline")
        _select_contains(page, "eeo[veteran]", candidate.get("eeo_veteran") or "Decline")

    fill_all_fields()
    page.wait_for_timeout(500)
    fill_all_fields()  # second pass after any late resume-parse writes
    street = (candidate.get("street") or "").strip()

    OUT.mkdir(parents=True, exist_ok=True)
    shot = OUT / f"lever_{int(time.time())}.png"
    page.screenshot(path=str(shot), full_page=True)

    if not street:
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="blocked",
            message="Street address missing in candidate.local.json — required by this Lever form.",
            screenshot=str(shot),
        )

    has_captcha = page.locator("iframe[src*='hcaptcha'], iframe[src*='captcha']").count() > 0
    if not submit:
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="filled_needs_review",
            message="Form filled and resume attached (submit=false).",
            screenshot=str(shot),
        )

    # Try submit
    submit_btn = page.get_by_role("button", name=re.compile(r"submit application", re.I))
    if submit_btn.count() == 0:
        submit_btn = page.locator('button:has-text("Submit"), input[type=submit]')
    try:
        submit_btn.first.click(timeout=5000)
    except Exception as exc:
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="error",
            message=f"Could not click submit: {exc}",
            screenshot=str(shot),
        )

    page.wait_for_timeout(3500)
    shot2 = OUT / f"lever_after_{int(time.time())}.png"
    page.screenshot(path=str(shot2), full_page=True)
    body = page.content().lower()
    url_now = page.url.lower()

    if "thank" in body or "application submitted" in body or "/thanks" in url_now or "success" in body:
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="submitted",
            message="Application appears submitted.",
            screenshot=str(shot2),
        )

    if has_captcha or "captcha" in body or page.locator("iframe[src*='hcaptcha']").count():
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="filled_needs_captcha",
            message="Form filled + resume uploaded, but hCaptcha blocked auto-submit. Open the apply URL, captcha is the only remaining step (fields may need a quick re-check).",
            screenshot=str(shot2),
        )

    return ApplyResult(
        job_id=job_id,
        company=job["company"],
        title=job["title"],
        url=job["url"],
        status="filled_needs_review",
        message="Submitted click sent but confirmation page not detected. Check screenshot / email.",
        screenshot=str(shot2),
    )


def apply_workday(page: Page, job: dict, candidate: dict, resume: Path, submit: bool) -> ApplyResult:
    """Best-effort Workday apply: open posting and start application."""
    job_id = job.get("id") or job["url"]
    page.goto(job["url"], wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(2500)
    OUT.mkdir(parents=True, exist_ok=True)
    shot = OUT / f"workday_{int(time.time())}.png"
    page.screenshot(path=str(shot), full_page=True)

    # Click Apply
    clicked = False
    for pattern in (r"^Apply$", r"Apply Now", r"Start Your Application", r"Autofill with Resume"):
        loc = page.get_by_role("button", name=re.compile(pattern, re.I))
        if loc.count() == 0:
            loc = page.get_by_role("link", name=re.compile(pattern, re.I))
        if loc.count():
            try:
                loc.first.click(timeout=4000)
                clicked = True
                page.wait_for_timeout(2500)
                break
            except Exception:
                pass

    # Try upload resume if file input appears
    file_inputs = page.locator('input[type=file]')
    uploaded = False
    if file_inputs.count():
        try:
            file_inputs.first.set_input_files(str(resume))
            uploaded = True
            page.wait_for_timeout(1500)
        except Exception:
            pass

    # Common identity fields
    for sel, val in [
        ('input[data-automation-id="legalNameSection_firstName"]', candidate["full_name"].split()[0]),
        ('input[data-automation-id="legalNameSection_lastName"]', candidate["full_name"].split()[-1]),
        ('input[data-automation-id="email"]', candidate["email"]),
        ('input[type=email]', candidate["email"]),
        ('input[data-automation-id="phone-number"]', candidate["phone"]),
    ]:
        if page.locator(sel).count():
            try:
                page.locator(sel).first.fill(val)
            except Exception:
                pass

    shot2 = OUT / f"workday_filled_{int(time.time())}.png"
    page.screenshot(path=str(shot2), full_page=True)

    if not clicked:
        return ApplyResult(
            job_id=job_id,
            company=job["company"],
            title=job["title"],
            url=job["url"],
            status="blocked",
            message="Workday Apply button not found (page may require login or geo block).",
            screenshot=str(shot2),
        )

    msg = "Workday application started"
    if uploaded:
        msg += ", resume attached"
    msg += ". Multi-step Workday flows often need account creation — complete remaining steps in the opened flow / screenshot."
    return ApplyResult(
        job_id=job_id,
        company=job["company"],
        title=job["title"],
        url=job["url"],
        status="filled_needs_review",
        message=msg,
        screenshot=str(shot2),
    )


def apply_linkedin(page: Page, job: dict, candidate: dict, resume: Path, submit: bool) -> ApplyResult:
    job_id = job.get("id") or job["url"]
    page.goto(job["url"], wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(2500)
    OUT.mkdir(parents=True, exist_ok=True)
    shot = OUT / f"linkedin_{int(time.time())}.png"
    page.screenshot(path=str(shot), full_page=True)
    return ApplyResult(
        job_id=job_id,
        company=job["company"],
        title=job["title"],
        url=job["url"],
        status="blocked",
        message="LinkedIn Easy Apply requires your LinkedIn login session. Use Apply Center's 'Open + copy profile' or sign in once in a persistent browser profile.",
        screenshot=str(shot),
    )


def apply_generic(page: Page, job: dict, candidate: dict, resume: Path, submit: bool) -> ApplyResult:
    job_id = job.get("id") or job["url"]
    page.goto(job["url"], wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1500)
    OUT.mkdir(parents=True, exist_ok=True)
    shot = OUT / f"generic_{int(time.time())}.png"
    page.screenshot(path=str(shot), full_page=True)
    return ApplyResult(
        job_id=job_id,
        company=job["company"],
        title=job["title"],
        url=job["url"],
        status="skipped",
        message="No dedicated automator for this host yet — opened posting for manual/one-click handoff.",
        screenshot=str(shot),
    )


def run_apply(job: dict, *, submit: bool = True, headed: bool = False) -> ApplyResult:
    candidate = load_candidate()
    resume = resume_path(candidate)
    platform = platform_for(job["url"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            if platform == "lever":
                result = apply_lever(page, job, candidate, resume, submit)
            elif platform == "workday":
                result = apply_workday(page, job, candidate, resume, submit)
            elif platform == "linkedin":
                result = apply_linkedin(page, job, candidate, resume, submit)
            else:
                result = apply_generic(page, job, candidate, resume, submit)
        except PlaywrightTimeout as exc:
            result = ApplyResult(
                job_id=job.get("id") or job["url"],
                company=job["company"],
                title=job["title"],
                url=job["url"],
                status="error",
                message=f"Timeout: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            result = ApplyResult(
                job_id=job.get("id") or job["url"],
                company=job["company"],
                title=job["title"],
                url=job["url"],
                status="error",
                message=str(exc),
            )
        finally:
            browser.close()

    # Persist local stage
    if result.status == "submitted":
        save_job_stage(job["url"], "Applied", result.to_dict())
    elif result.status in {"filled_needs_captcha", "filled_needs_review"}:
        save_job_stage(job["url"], "Ready to Apply", result.to_dict())

    log_path = OUT / "last_results.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(result.to_dict()) + "\n")
    return result


def run_apply_all_ready(*, submit: bool = True) -> list[ApplyResult]:
    results = []
    for job in load_jobs():
        if job.get("stage") != "Ready to Apply":
            continue
        # Skip known non-automatable hosts in batch unless lever/workday
        plat = platform_for(job["url"])
        if plat in {"linkedin", "indeed", "remotive", "generic"}:
            results.append(
                ApplyResult(
                    job_id=job.get("id") or job["url"],
                    company=job["company"],
                    title=job["title"],
                    url=job["url"],
                    status="skipped",
                    message=f"Batch skip for {plat} — use single-job apply or LinkedIn login profile.",
                )
            )
            continue
        results.append(run_apply(job, submit=submit, headed=False))
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="One-click job apply")
    parser.add_argument("--job-url", help="Apply to a specific job URL")
    parser.add_argument("--all-ready", action="store_true", help="Apply to all Ready to Apply jobs")
    parser.add_argument("--no-submit", action="store_true", help="Fill only, do not click submit")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    submit = not args.no_submit
    if args.all_ready:
        for r in run_apply_all_ready(submit=submit):
            print(json.dumps(r.to_dict(), indent=2))
    elif args.job_url:
        jobs = [j for j in load_jobs() if j["url"] == args.job_url]
        if not jobs:
            jobs = [{"id": "adhoc", "title": "Adhoc", "company": "Unknown", "url": args.job_url}]
        print(json.dumps(run_apply(jobs[0], submit=submit, headed=args.headed).to_dict(), indent=2))
    else:
        parser.print_help()
