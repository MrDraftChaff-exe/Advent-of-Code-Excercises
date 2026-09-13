#!/usr/bin/env python3
"""Split the 395-still zip into 50-episode packs browsers can actually save."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

EPISODE_RE = re.compile(r"(?:^|/)(\d{3})-")
PACK_SIZE = 50


def episode_num(name: str) -> int | None:
    match = EPISODE_RE.search(name)
    return int(match.group(1)) if match else None


def pack_ranges(count: int = 395, size: int = PACK_SIZE) -> list[tuple[int, int]]:
    return [
        (start, min(start + size - 1, count))
        for start in range(1, count + 1, size)
    ]


def write_packs(src: Path, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(src) as zin:
        members = [
            (name, episode_num(name))
            for name in zin.namelist()
            if not name.endswith("/")
        ]
        numbered = [(name, n) for name, n in members if n is not None]
        count = max(n for _, n in numbered)
        for start, end in pack_ranges(count):
            out = dest / f"facts-or-whacks-stills-{start:03d}-{end:03d}.zip"
            with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zout:
                for name, n in numbered:
                    if start <= n <= end:
                        zout.writestr(name, zin.read(name))
            written.append(out)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src",
        type=Path,
        default=Path("public/catalog/facts-or-whacks-395-stills.zip"),
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("public/catalog"),
    )
    args = parser.parse_args()
    if not args.src.is_file():
        raise SystemExit(f"missing source zip: {args.src}")
    for path in write_packs(args.src, args.dest):
        print(f"{path}  {path.stat().st_size}")


if __name__ == "__main__":
    main()
