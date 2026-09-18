#!/usr/bin/env python3
"""Local 1-click Apply Center for Montanna's curated jobs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, send_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_engine import (  # noqa: E402
    load_candidate,
    load_jobs,
    platform_for,
    resume_path,
    run_apply,
    run_apply_all_ready,
    save_job_stage,
)

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Montanna — 1-Click Apply Center</title>
  <style>
    :root {
      --bg: #0f1c17;
      --panel: #173028;
      --ink: #e8f2ec;
      --muted: #9bb5a8;
      --accent: #3ecf8e;
      --warn: #f0c14a;
      --danger: #ff6b6b;
      --card: #1d3a30;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(1200px 600px at 10% -10%, #1f4a3a 0%, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #243d55 0%, transparent 50%),
        var(--bg);
      color: var(--ink);
      min-height: 100vh;
    }
    main { max-width: 980px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 2rem; margin: 0 0 8px; letter-spacing: -0.02em; }
    .sub { color: var(--muted); margin-bottom: 24px; }
    .banner {
      background: #2a2412;
      border: 1px solid #6d5a1f;
      color: #ffe7a0;
      padding: 12px 14px;
      border-radius: 10px;
      margin-bottom: 18px;
    }
    .banner a { color: #fff1c2; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 22px; }
    button, .btn {
      appearance: none; border: 0; cursor: pointer;
      background: var(--accent); color: #062016; font-weight: 700;
      padding: 12px 16px; border-radius: 10px; font-size: 0.95rem;
      text-decoration: none; display: inline-flex; align-items: center;
    }
    button.secondary, .btn.secondary { background: #2c4a3e; color: var(--ink); }
    button:disabled { opacity: 0.55; cursor: wait; }
    .job {
      background: var(--card);
      border: 1px solid #2f5647;
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 12px;
      display: grid;
      gap: 10px;
    }
    .job h2 { margin: 0; font-size: 1.1rem; }
    .meta { color: var(--muted); font-size: 0.92rem; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .pill {
      display: inline-block; padding: 4px 8px; border-radius: 999px;
      background: #25483b; color: var(--ink); font-size: 0.78rem;
    }
    .pill.ready { background: #1d4d38; color: #9dffc9; }
    .pill.applied { background: #1d3f5a; color: #9fd0ff; }
    .log {
      margin-top: 18px; background: #0c1612; border-radius: 12px;
      padding: 12px; white-space: pre-wrap; font-family: ui-monospace, monospace;
      font-size: 0.82rem; min-height: 80px; border: 1px solid #234037;
    }
    label { display:block; margin: 8px 0 4px; color: var(--muted); font-size: 0.85rem; }
    input[type=text], input[type=email], input[type=tel] {
      width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #35584a;
      background: #10241c; color: var(--ink);
    }
    .profile {
      background: var(--panel); border-radius: 14px; padding: 14px; margin-bottom: 18px;
      border: 1px solid #2b4c3f;
    }
    .grid2 { display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    @media (max-width: 700px) { .grid2 { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>1-Click Apply Center</h1>
  <p class="sub">Montanna Marsh · fills the application, attaches resume, submits when the site allows.</p>

  {% if not street %}
  <div class="banner">
    Street address is empty. Quantum Health (and many ATS forms) require it.
    Enter it below, save, then use <b>Apply</b>.
  </div>
  {% endif %}

  <div class="profile">
    <form method="post" action="/profile">
      <div class="grid2">
        <div>
          <label>Full name</label>
          <input name="full_name" value="{{ c.full_name }}" />
        </div>
        <div>
          <label>Email</label>
          <input name="email" type="email" value="{{ c.email }}" />
        </div>
        <div>
          <label>Phone</label>
          <input name="phone_display" value="{{ c.phone_display }}" />
        </div>
        <div>
          <label>Street address (required for Lever)</label>
          <input name="street" value="{{ c.street }}" placeholder="123 Main St" />
        </div>
        <div>
          <label>City / State / ZIP / Country</label>
          <input name="city_state_zip_country" value="{{ c.city_state_zip_country }}" />
        </div>
        <div>
          <label>Desired hourly pay</label>
          <input name="desired_hourly" value="{{ c.desired_hourly }}" />
        </div>
      </div>
      <div class="actions" style="margin-top:12px;margin-bottom:0">
        <button type="submit" class="secondary">Save profile</button>
        <a class="btn secondary" href="/resume">Download resume</a>
      </div>
    </form>
  </div>

  <div class="actions">
    <button id="applyAll" onclick="applyAll()">Apply all Ready jobs</button>
    <button class="secondary" onclick="location.reload()">Refresh</button>
  </div>

  {% for job in jobs %}
  <div class="job" data-url="{{ job.url }}">
    <h2>{{ job.title }}</h2>
    <div class="meta">{{ job.company }} · {{ job.location }} · {{ job.pay }}</div>
    <div class="row">
      <span class="pill {{ 'ready' if job.stage=='Ready to Apply' else ('applied' if job.stage=='Applied' else '') }}">{{ job.stage }}</span>
      <span class="pill">{{ platforms[job.url] }}</span>
      <span class="pill">fit {{ job.fit_score }}</span>
    </div>
    <div class="row">
      <button onclick="applyOne(this, '{{ job.url }}')" {% if job.stage=='Applied' %}disabled{% endif %}>
        {% if platforms[job.url] == 'lever' %}1-Click Apply{% else %}Auto-Apply (best effort){% endif %}
      </button>
      <a class="btn secondary" href="{{ job.url }}" target="_blank" rel="noopener">Open posting</a>
    </div>
  </div>
  {% endfor %}

  <h2 style="margin-top:28px">Activity</h2>
  <div class="log" id="log">Ready.</div>
</main>
<script>
async function applyOne(btn, url) {
  const log = document.getElementById('log');
  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = 'Applying…';
  log.textContent = 'Applying to ' + url + ' …';
  try {
    const res = await fetch('/api/apply', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, submit: true})
    });
    const data = await res.json();
    log.textContent = JSON.stringify(data, null, 2);
    if (data.status === 'submitted') location.reload();
  } catch (e) {
    log.textContent = String(e);
  } finally {
    btn.disabled = false;
    btn.textContent = old;
  }
}
async function applyAll() {
  const btn = document.getElementById('applyAll');
  const log = document.getElementById('log');
  btn.disabled = true;
  log.textContent = 'Applying all Ready jobs…';
  try {
    const res = await fetch('/api/apply-all', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({submit:true})});
    const data = await res.json();
    log.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    log.textContent = String(e);
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


@app.get("/")
def home():
    c = load_candidate()
    jobs = load_jobs()
    platforms = {j["url"]: platform_for(j["url"]) for j in jobs}
    return render_template_string(
        PAGE,
        c=c,
        jobs=jobs,
        platforms=platforms,
        street=(c.get("street") or "").strip(),
    )


@app.post("/profile")
def save_profile():
    path = ROOT / "data" / "candidate.local.json"
    c = load_candidate()
    for key in (
        "full_name",
        "email",
        "phone_display",
        "street",
        "city_state_zip_country",
        "desired_hourly",
    ):
        if key in request.form:
            c[key] = request.form.get(key, "").strip()
    # keep digits-only phone too
    digits = "".join(ch for ch in c.get("phone_display", "") if ch.isdigit())
    if digits:
        c["phone"] = digits
    path.write_text(json.dumps(c, indent=2) + "\n")
    return redirect("/")


@app.get("/resume")
def download_resume():
    path = resume_path(load_candidate())
    return send_file(path, as_attachment=True, download_name=path.name)


@app.post("/api/apply")
def api_apply():
    payload = request.get_json(force=True, silent=True) or {}
    url = payload.get("url")
    submit = bool(payload.get("submit", True))
    jobs = [j for j in load_jobs() if j["url"] == url]
    if not jobs:
        return jsonify({"status": "error", "message": "Unknown job URL"}), 404
    result = run_apply(jobs[0], submit=submit, headed=False)
    return jsonify(result.to_dict())


@app.post("/api/apply-all")
def api_apply_all():
    payload = request.get_json(force=True, silent=True) or {}
    submit = bool(payload.get("submit", True))
    results = [r.to_dict() for r in run_apply_all_ready(submit=submit)]
    return jsonify({"results": results})


if __name__ == "__main__":
    print("Apply Center → http://127.0.0.1:8787")
    app.run(host="0.0.0.0", port=8787, debug=False)
