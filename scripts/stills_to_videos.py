#!/usr/bin/env python3
"""Turn 9:16 catalog stills into 30s H.264 MP4s with the original pad."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

EPISODE_RE = re.compile(r"(?:^|/)(\d{3})-[^/]+\.(?:webp|png|jpg|jpeg)$", re.I)
PACK_SIZE = 50


def episode_num(name: str) -> int | None:
    match = EPISODE_RE.search(name.replace("\\", "/"))
    return int(match.group(1)) if match else None


def pack_ranges(count: int = 395, size: int = PACK_SIZE) -> list[tuple[int, int]]:
    return [
        (start, min(start + size - 1, count))
        for start in range(1, count + 1, size)
    ]


def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg is required")
    return path


def encode_one(
    ffmpeg: str,
    still: Path,
    audio: Path,
    dest: Path,
    seconds: float,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(still),
        "-i",
        str(audio),
        "-t",
        f"{seconds:.3f}",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "28",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-shortest",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    subprocess.run(cmd, check=True)
    return dest


def collect_stills(src: Path) -> list[Path]:
    if src.is_file() and src.suffix.lower() == ".zip":
        extract = src.parent / "_stills_unpacked"
        extract.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(src) as zf:
            zf.extractall(extract)
        src = extract
    stills = [
        p
        for p in src.rglob("*")
        if p.is_file() and episode_num(p.name) is not None
    ]
    stills.sort(key=lambda p: episode_num(p.name) or 0)
    return stills


def write_video_packs(video_dir: Path, dest: Path, count: int) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    videos = {
        episode_num(p.name): p
        for p in video_dir.glob("*.mp4")
        if episode_num(p.name) is not None
    }
    written: list[Path] = []
    for start, end in pack_ranges(count):
        out = dest / f"facts-or-whacks-videos-{start:03d}-{end:03d}.zip"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zf:
            for n in range(start, end + 1):
                clip = videos.get(n)
                if clip:
                    zf.write(clip, f"facts-or-whacks-videos/{clip.name}")
        written.append(out)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stills",
        type=Path,
        default=Path("public/catalog/facts-or-whacks-395-stills.zip"),
    )
    parser.add_argument(
        "--audio",
        type=Path,
        default=Path("public/audio/facts-or-whacks-pad-30s.wav"),
    )
    parser.add_argument("--out", type=Path, default=Path("dist/catalog-videos"))
    parser.add_argument("--packs", type=Path, default=Path("public/catalog"))
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-packs", action="store_true")
    args = parser.parse_args()
    if not args.audio.is_file():
        subprocess.run(
            [
                "python3",
                str(Path(__file__).with_name("make_pad_audio.py")),
                "--out",
                str(args.audio),
                "--seconds",
                str(args.seconds),
            ],
            check=True,
        )
    stills = collect_stills(args.stills)
    if args.limit:
        stills = stills[: args.limit]
    if not stills:
        raise SystemExit(f"no stills in {args.stills}")
    ffmpeg = ffmpeg_bin()
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"encoding {len(stills)} clips to {args.out}", flush=True)

    def job(still: Path) -> Path:
        n = episode_num(still.name)
        dest = args.out / f"{still.stem}.mp4"
        return encode_one(ffmpeg, still, args.audio, dest, args.seconds)

    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(job, still) for still in stills]
        for fut in as_completed(futures):
            path = fut.result()
            done += 1
            if done % 10 == 0 or done == len(stills):
                print(f"{done}/{len(stills)}  {path.name}", flush=True)
    if not args.skip_packs:
        packs = write_video_packs(
            args.out,
            args.packs,
            max(episode_num(p.name) or 0 for p in stills),
        )
        for pack in packs:
            print(pack, pack.stat().st_size)


if __name__ == "__main__":
    main()
