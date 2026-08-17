"""Validate product folders against KDP print rules."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from .specs import load_specs, product_dir, trim_box


def validate_product(slug: str) -> list[str]:
    errors: list[str] = []
    root = product_dir(slug)
    if not root.exists():
        return [f"Missing product folder: {root}"]

    meta_path = root / "meta.json"
    if not meta_path.exists():
        errors.append("meta.json missing")
        return errors

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    specs = load_specs()
    trim = meta.get("trim", "letter")
    if trim not in specs["trims"]:
        errors.append(f"Unknown trim: {trim}")

    pages_dir = root / "pages"
    pngs = sorted(pages_dir.glob("page-*.png")) if pages_dir.exists() else []
    designs = int(meta.get("designs", 0))
    if designs and len(pngs) < designs:
        errors.append(f"Expected {designs} page PNGs, found {len(pngs)}")

    dpi_target = int(specs["dpi"])
    width_in, height_in = trim_box(trim)
    for png in pngs[:5]:  # sample first pages
        with Image.open(png) as im:
            dpi = im.info.get("dpi", (0, 0))
            dpi_x = float(dpi[0]) if dpi else 0
            if dpi_x and dpi_x < dpi_target - 1:
                errors.append(f"{png.name}: DPI {dpi_x} < {dpi_target}")
            expected_w = int(round(width_in * dpi_target))
            expected_h = int(round(height_in * dpi_target))
            if im.size != (expected_w, expected_h):
                errors.append(
                    f"{png.name}: size {im.size} != expected {(expected_w, expected_h)} @ {dpi_target} DPI"
                )

    pdf = root / "interior.pdf"
    if pdf.exists():
        reader = PdfReader(str(pdf))
        page_count = len(reader.pages)
        meta_pages = meta.get("page_count_interior")
        if meta_pages and int(meta_pages) != page_count:
            errors.append(f"meta page_count_interior {meta_pages} != PDF pages {page_count}")
        if page_count < 24:
            errors.append(f"Interior has {page_count} pages; KDP minimum is 24")
        if page_count % 2 != 0:
            errors.append("Interior page count should be even")
        page = reader.pages[0]
        box = page.mediabox
        pw = float(box.width) / 72.0
        ph = float(box.height) / 72.0
        if abs(pw - width_in) > 0.02 or abs(ph - height_in) > 0.02:
            errors.append(f"PDF page size {pw:.3f}x{ph:.3f}in != trim {width_in}x{height_in}in")

    return errors
