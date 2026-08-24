#!/usr/bin/env python3
"""Batch-make 30s 9:16 videos and overlay a trendy-style audio bed.

Examples:
  python3 scripts/overlay_trendy_audio.py --csv facts-or-whacks-30-videos.csv
  python3 scripts/overlay_trendy_audio.py --input-dir ./clips --audio ./bed.mp3
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DURATION = 30.0
FPS = 30
WIDTH = 1080
HEIGHT = 1920
SR = 44100
BPM = 140
USER_AGENT = (
    "FactsOrWhacksBot/1.0 (educational history shorts; "
    "https://github.com/mrdraftchaff-exe/advent-of-code-excercises)"
)

FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_SANS = Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf")
FONT_SANS_MED = Path("/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf")

# Working Wikimedia Commons filenames (CSV URLs are often guessed / 404).
COMMONS_FILES = {
    1: "Sanzio 01.jpg",
    2: "Washington Crossing the Delaware by Emanuel Leutze, MMA-NYC, 1851.jpg",
    3: "Prise de la Bastille.jpg",
    4: "La bataille d'Austerlitz. 2 decembre 1805 (François Gérard).jpg",
    5: "Combats entre les insurgés de Saint-Domingue et les troupes françaises envoyées par Napoléon Bonaparte (1802-1803).jpg",
    6: "Loutherbourg, Coalbrookdale by Night.jpg",
    7: "Lewis and clark-expedition.jpg",
    8: "Official medallion of the British Anti-Slavery Society (1795).jpg",
    9: "Sutter's Mill.jpg",
    10: "Charles Darwin by Julia Margaret Cameron 2.jpg",
    11: "Battle of Antietam.jpg",
    12: "East and West Shaking hands at the laying of last rail Union Pacific Railroad.jpg",
    13: "Emperor Meiji.jpg",
    14: "JacktheRipper1888.jpg",
    15: "First flight2.jpg",
    16: "RMS Titanic 3.jpg",
    17: "Cheshire Regiment trench Somme 1916.jpg",
    18: "Kustodiev The Bolshevik.jpg",
    19: "Charleston at the Capitol LCCN93508925.jpg",
    20: "Synthetic Production of Penicillin TR1468.jpg",
    21: "Lange-MigrantMother02.jpg",
    22: "Into the Jaws of Death 23-0455M edit.jpg",
    23: "Into the Jaws of Death 23-0455M edit.jpg",
    24: "The arbeit macht frei gate in Auschwitz I.jpg",
    25: "PM Nehru addresses the nation from the Red Fort on 15 August 1947.jpg",
    26: "Aldrin Apollo 11.jpg",
    27: "March on Washington edit.jpg",
    28: "West and East Germans at the Brandenburg Gate in 1989.jpg",
    29: "Arpanet logical map, march 1977.png",
    30: "Mandela voting in 1994.jpg",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}


def slug(text: str) -> str:
    keep = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif keep and keep[-1] != "-":
            keep.append("-")
    return "".join(keep).strip("-")[:60] or "clip"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def ffprobe_json(path: Path) -> dict:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    return json.loads(out)


# --- trendy 30s bed (original; swap for a TikTok/CapCut sound if you want the algorithm boost)


def _place(buf: np.ndarray, start: int, sig: np.ndarray) -> None:
    if start >= len(buf) or start < 0:
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


def _kick(n: int, f0: float = 52.0) -> np.ndarray:
    t = np.arange(n) / SR
    freq = f0 * np.exp(-t * 14.0) + 28.0
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-t * 9.0)
    click = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 80.0) * 0.25
    return body + click


def _snare(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n) * np.exp(-t * 18.0)
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 16.0)
    return 0.55 * noise + 0.45 * tone


def _hat(n: int, closed: bool = True) -> np.ndarray:
    rng = np.random.default_rng(3)
    t = np.arange(n) / SR
    decay = 90.0 if closed else 18.0
    noise = rng.standard_normal(n)
    # crude highpass
    hp = np.diff(noise, prepend=noise[0])
    return hp * np.exp(-t * decay)


def _bass(n: int, freq: float) -> np.ndarray:
    t = np.arange(n) / SR
    # 808-style pitch drop + saturated sine
    f = freq * np.exp(-t * 1.8) + freq * 0.15
    phase = 2 * np.pi * np.cumsum(f) / SR
    wave = np.sin(phase)
    wave = np.tanh(2.4 * wave)
    env = np.minimum(1.0, t / 0.012) * np.exp(-t * 3.2)
    return wave * env


def _bell(n: int, freq: float) -> np.ndarray:
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / 0.008) * np.exp(-t * 6.5)
    sig = (
        0.65 * np.sin(2 * np.pi * freq * t)
        + 0.22 * np.sin(2 * np.pi * freq * 2.01 * t)
        + 0.13 * np.sin(2 * np.pi * freq * 3.02 * t)
    )
    return sig * env


def _pad(n: int, freqs: list[float]) -> np.ndarray:
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (n / SR - t) / 0.6)
    env = np.clip(env, 0, 1)
    sig = np.zeros(n)
    for i, f in enumerate(freqs):
        sig += np.sin(2 * np.pi * f * t + i * 0.3) / len(freqs)
        sig += 0.15 * np.sin(2 * np.pi * (f * 2) * t)
    return sig * env * 0.22


def generate_trendy_bed(path: Path, seconds: float = DURATION) -> Path:
    """Write an original dark-cinematic trap bed (TikTok-adjacent, not a ripped sound)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(SR * seconds)
    mix = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(140)

    beat = 60.0 / BPM
    step = beat / 4.0  # 16th
    n_steps = int(seconds / step)

    # D# minor-ish (classic dark / phonk-adjacent palette)
    ds1, fs1, gs1, as1, cs2 = 38.89, 46.25, 51.91, 58.27, 69.30
    bass_loop = [ds1, 0, 0, ds1, 0, 0, as1, 0, cs2, 0, 0, ds1, fs1, 0, gs1, 0]
    bell_loop = [311.13, 0, 369.99, 0, 311.13, 0, 0, 415.30, 466.16, 0, 311.13, 0, 277.18, 0, 233.08, 0]

    for i in range(n_steps):
        start = int(i * step * SR)
        # kicks on 1 and 3, plus a pickup
        if i % 8 == 0:
            _place(mix, start, _kick(int(0.28 * SR)) * 0.95)
        elif i % 8 == 6 and (i // 16) % 2 == 1:
            _place(mix, start, _kick(int(0.18 * SR)) * 0.55)
        # snare / clap on 2 and 4
        if i % 8 == 4:
            _place(mix, start, _snare(int(0.22 * SR)) * 0.7)
        # hats
        hat_vel = 0.18 if i % 2 == 0 else 0.10
        if i % 16 == 14:
            # roll
            for r in range(4):
                _place(mix, start + int(r * step * SR / 4), _hat(int(0.04 * SR)) * 0.16)
        else:
            _place(mix, start, _hat(int(0.05 * SR), closed=True) * hat_vel)
        # 808
        b = bass_loop[i % len(bass_loop)]
        if b:
            _place(mix, start, _bass(int(0.55 * SR), b) * 0.7)
        # melody after bar 1
        if i >= 16:
            m = bell_loop[i % len(bell_loop)]
            if m:
                _place(mix, start, _bell(int(0.35 * SR), m) * 0.22)

    # pads, two 8-bar drones
    pad_len = int(8 * 4 * beat * SR)
    _place(mix, 0, _pad(min(pad_len, n), [155.56, 233.08, 311.13]))
    _place(mix, int(8 * beat * SR), _pad(min(pad_len, n), [185.00, 233.08, 311.13]))
    _place(mix, int(16 * beat * SR), _pad(min(pad_len, n), [155.56, 207.65, 311.13]))

    # riser into the last 6s
    rise_start = int(24.0 * SR)
    rise_n = min(int(2.0 * SR), n - rise_start)
    if rise_n > 0:
        t = np.arange(rise_n) / SR
        rise = rng.standard_normal(rise_n) * (t / 2.0) ** 2 * 0.15
        _place(mix, rise_start, rise)
        _place(mix, int(26.0 * SR), _kick(int(0.4 * SR)) * 1.1)

    # tape hiss
    mix += rng.standard_normal(n) * 0.008

    # fade in/out + peak normalize
    fade_in = int(0.12 * SR)
    fade_out = int(0.9 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)
    peak = np.max(np.abs(mix)) or 1.0
    mix = mix / peak * 0.89
    mix = np.tanh(mix * 1.05)

    # stereo width
    delay = int(0.012 * SR)
    right = np.zeros_like(mix)
    right[delay:] = mix[:-delay] * 0.92
    right += mix * 0.15
    left = mix
    stereo = np.stack([left, np.clip(right, -0.99, 0.99)], axis=1)
    pcm = np.clip(stereo, -0.99, 0.99)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return path


# --- stills / overlays


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.replace("|", " ").split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines[:4]


def cover_crop(im: Image.Image, w: int, h: int) -> Image.Image:
    im = im.convert("RGB")
    scale = max(w / im.width, h / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = int((nh - h) * 0.28)  # bias up — faces / architecture sit high
    top = max(0, min(top, nh - h))
    cropped = im.crop((left, top, left + w, top + h))
    cropped = ImageEnhance.Contrast(cropped).enhance(1.08)
    cropped = ImageEnhance.Color(cropped).enhance(0.92)
    cropped = ImageEnhance.Brightness(cropped).enhance(0.88)
    return cropped


def make_gradient_overlay() -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(0, 280):
        a = int(150 * (1 - y / 280))
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))
    for y in range(HEIGHT - 820, HEIGHT):
        t = (y - (HEIGHT - 820)) / 820
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, int(210 * t)))
    return img


def make_card_png(path: Path, title: str, hook: str, fact: str, handle: str = "@FactsOrWhacks") -> Path:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    img = Image.alpha_composite(img, make_gradient_overlay())
    draw = ImageDraw.Draw(img)
    title_f = font(FONT_SERIF, 54)
    hook_f = font(FONT_SANS, 46)
    fact_f = font(FONT_SANS_MED, 40)
    meta_f = font(FONT_SANS_MED, 28)

    draw.text((WIDTH // 2, 96), handle, font=meta_f, fill=(255, 255, 255, 210), anchor="mt")

    # title box
    title_lines = wrap_text(draw, title.upper(), title_f, 900)
    y = 1280
    for line in title_lines:
        tw = draw.textlength(line, font=title_f)
        box = [(WIDTH - tw) / 2 - 28, y - 10, (WIDTH + tw) / 2 + 28, y + 62]
        draw.rounded_rectangle(box, radius=10, fill=(0, 0, 0, 140), outline=(255, 255, 255, 70), width=1)
        draw.text((WIDTH // 2, y), line, font=title_f, fill=(255, 255, 255, 255), anchor="mt")
        y += 70

    hook_lines = wrap_text(draw, hook, hook_f, 860) if hook else []
    fact_lines = wrap_text(draw, fact, fact_f, 860) if fact and fact.lower() != hook.lower() else []
    for line, fnt in [(ln, hook_f) for ln in hook_lines] + [(ln, fact_f) for ln in fact_lines]:
        if y > 1760:
            break
        tw = draw.textlength(line, font=fnt)
        box = [(WIDTH - tw) / 2 - 24, y + 8, (WIDTH + tw) / 2 + 24, y + 62]
        draw.rounded_rectangle(box, radius=10, fill=(0, 0, 0, 150), outline=(255, 255, 255, 50), width=1)
        draw.text((WIDTH // 2, y + 14), line, font=fnt, fill=(255, 255, 255, 245), anchor="mt")
        y += 64

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


# --- commons download


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 500, 502, 503} and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise RuntimeError(f"failed GET {url}")


def http_download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp, open(tmp, "wb") as fh:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    fh.write(chunk)
            tmp.replace(dest)
            return
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 500, 502, 503} and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise RuntimeError(f"failed download {url}")


def resolve_commons_thumbs(files: list[str]) -> dict[str, str]:
    """Map 'File:Name' -> thumbnail/original URL."""
    titles = [f if f.startswith("File:") else f"File:{f}" for f in files]
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": "1280",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = http_json(url)
    out: dict[str, str] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        title = page.get("title", "")
        if "missing" in page:
            continue
        info = (page.get("imageinfo") or [{}])[0]
        href = info.get("thumburl") or info.get("url")
        if href:
            out[title] = href.split("?", 1)[0]
    return out


# --- ffmpeg render


def render_image_video(
    still: Path,
    overlay: Path,
    audio: Path,
    dest: Path,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Ken Burns: source still is 1296x2304; pan/zoom via crop over 30s.
    vf = (
        f"[0:v]fps={FPS},scale={int(WIDTH * 1.2)}:{int(HEIGHT * 1.2)},"
        f"crop={WIDTH}:{HEIGHT}:x='(in_w-{WIDTH})*t/{DURATION}':"
        f"y='(in_h-{HEIGHT})*0.25+(in_h-{HEIGHT})*0.5*t/{DURATION}',"
        "eq=contrast=1.05:brightness=-0.04:saturation=0.92[bg];"
        "[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(still),
        "-i",
        str(overlay),
        "-i",
        str(audio),
        "-filter_complex",
        vf,
        "-map",
        "[v]",
        "-map",
        "2:a:0",
        "-t",
        str(DURATION),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(SR),
        "-ac",
        "2",
        "-shortest",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    run(cmd)


def render_video_file(src: Path, audio: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Fit to 9:16, lock to 30s, replace soundtrack with the bed.
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-i",
        str(audio),
        "-vf",
        vf,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-t",
        str(DURATION),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(SR),
        "-ac",
        "2",
        "-shortest",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    run(cmd)


def prepare_still(src: Path, dest: Path) -> Path:
    im = Image.open(src)
    if im.mode not in {"RGB", "L"}:
        im = im.convert("RGB")
    cover = cover_crop(im, int(WIDTH * 1.2), int(HEIGHT * 1.2))
    dest.parent.mkdir(parents=True, exist_ok=True)
    cover.save(dest, quality=90)
    return dest


def fact_list(row: dict) -> list[str]:
    hook = (row.get("hook") or "").strip()
    bullets = [b.strip() for b in (row.get("on_screen_bullets") or "").split("|") if b.strip()]
    # Hook first, then unique bullets — 6 cards ≈ 5s each.
    cards = [hook] if hook else []
    for b in bullets:
        if b.lower() not in {c.lower() for c in cards}:
            cards.append(b)
    return (cards or [row.get("title") or "Facts or Whacks"])[:6]


def timed_overlay(path: Path, title: str, hook: str, facts: list[str]) -> Path:
    punch = facts[0] if facts else hook
    extra = facts[1] if len(facts) > 1 else ""
    return make_card_png(path, title, punch, extra)


def verify_clip(path: Path) -> tuple[bool, str]:
    info = ffprobe_json(path)
    dur = float(info.get("format", {}).get("duration") or 0)
    streams = info.get("streams") or []
    has_v = any(s.get("codec_type") == "video" for s in streams)
    has_a = any(s.get("codec_type") == "audio" for s in streams)
    ok = has_v and has_a and 29.0 <= dur <= 31.0
    return ok, f"dur={dur:.2f}s video={has_v} audio={has_a}"


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def process_csv(csv_path: Path, out_dir: Path, audio: Path, limit: int | None) -> list[Path]:
    rows = load_csv(csv_path)
    if limit:
        rows = rows[:limit]
    still_dir = out_dir.parent / "stills"
    overlay_dir = out_dir.parent / "overlays"
    still_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)

    files = [COMMONS_FILES[int(r["topic_number"])] for r in rows if int(r["topic_number"]) in COMMONS_FILES]
    thumbs = resolve_commons_thumbs(files)
    print(f"Resolved {len(thumbs)} Commons stills", flush=True)

    rendered: list[Path] = []
    for row in rows:
        num = int(row["topic_number"])
        title = row["title"]
        key = f"File:{COMMONS_FILES[num]}"
        url = thumbs.get(key)
        if not url:
            print(f"SKIP {num} {title}: no Commons URL", flush=True)
            continue
        stem = f"{num:02d}-{slug(title)}"
        raw = still_dir / f"{stem}-raw{Path(url).suffix or '.jpg'}"
        still = still_dir / f"{stem}.jpg"
        overlay = overlay_dir / f"{stem}.png"
        dest = out_dir / f"{stem}.mp4"
        if dest.exists():
            ok, msg = verify_clip(dest)
            if ok:
                print(f"skip    {num} {title} ({msg})", flush=True)
                rendered.append(dest)
                continue
        if not raw.exists() or raw.stat().st_size < 2000:
            print(f"download {num} {title}", flush=True)
            http_download(url, raw)
            time.sleep(0.4)
        prepare_still(raw, still)
        timed_overlay(overlay, title, row.get("hook") or "", fact_list(row))
        print(f"render  {num} {title} -> {dest.name}", flush=True)
        render_image_video(still, overlay, audio, dest)
        ok, msg = verify_clip(dest)
        print(f"  {msg}{' OK' if ok else ' FAIL'}", flush=True)
        if not ok:
            raise SystemExit(f"verification failed for {dest}")
        rendered.append(dest)
    return rendered


def process_input_dir(input_dir: Path, out_dir: Path, audio: Path, limit: int | None) -> list[Path]:
    files = sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS
    )
    if limit:
        files = files[:limit]
    if not files:
        raise SystemExit(f"No image/video files in {input_dir}")
    overlay_dir = out_dir.parent / "overlays"
    still_dir = out_dir.parent / "stills"
    rendered: list[Path] = []
    for i, src in enumerate(files, 1):
        dest = out_dir / f"{i:02d}-{slug(src.stem)}.mp4"
        print(f"render {src.name} -> {dest.name}", flush=True)
        if src.suffix.lower() in VIDEO_EXTS:
            render_video_file(src, audio, dest)
        else:
            still = still_dir / f"{slug(src.stem)}.jpg"
            overlay = overlay_dir / f"{slug(src.stem)}.png"
            prepare_still(src, still)
            make_card_png(overlay, src.stem.replace("-", " "), src.stem, "30 seconds. Trendy bed.")
            render_image_video(still, overlay, audio, dest)
        ok, msg = verify_clip(dest)
        print(f"  {msg}{' OK' if ok else ' FAIL'}", flush=True)
        if not ok:
            raise SystemExit(f"verification failed for {dest}")
        rendered.append(dest)
    return rendered


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=Path, help="Facts-or-Whacks CSV (one still per topic)")
    src.add_argument("--input-dir", type=Path, help="Folder of images or videos")
    p.add_argument("--audio", type=Path, help="Custom 30s bed (mp3/wav/m4a). Generated if omitted.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "videos")
    p.add_argument("--limit", type=int, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.audio:
        audio = args.audio
        if not audio.exists():
            raise SystemExit(f"Audio not found: {audio}")
    else:
        audio = out_dir.parent / "audio" / "trendy_30s.wav"
        if not audio.exists():
            print(f"Generating 30s trendy bed -> {audio}", flush=True)
            generate_trendy_bed(audio, DURATION)
        else:
            print(f"Reusing {audio}", flush=True)

    if args.csv:
        clips = process_csv(args.csv.resolve(), out_dir, audio, args.limit)
    else:
        clips = process_input_dir(args.input_dir.resolve(), out_dir, audio, args.limit)

    print(f"\nWrote {len(clips)} x {int(DURATION)}s clips with audio overlay:")
    for c in clips:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
