#!/usr/bin/env python3
"""Quiet Places inkify — thin wrapper around inkify_bold_easy (STYLE.md)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inkify_bold_easy import to_ink  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "products" / "quiet-places-40" / "art-source"

def main() -> None:
    src_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/gen/quiet-places")
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("qp-gen-*.png"))
    if not files:
        raise SystemExit(f"No qp-gen-*.png in {src_dir}")
    for i, f in enumerate(files, start=1):
        to_ink(f, OUT / f"qp2-{i:02d}.png")
    print(f"wrote {len(files)} pages -> {OUT}")

if __name__ == "__main__":
    main()
