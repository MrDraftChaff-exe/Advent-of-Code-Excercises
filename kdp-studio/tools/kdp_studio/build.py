"""Build KDP-ready interior and cover-dimension helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .specs import gutter_for_pages, load_specs, spine_width, trim_box


def blank_page_png(path: Path, trim: str, dpi: int = 300) -> Path:
    width_in, height_in = trim_box(trim)
    w = int(round(width_in * dpi))
    h = int(round(height_in * dpi))
    Image.new("L", (w, h), 255).save(path, dpi=(dpi, dpi))
    return path


def build_interior_pdf(
    page_images: list[Path],
    out_pdf: Path,
    trim: str = "letter",
    single_sided: bool = True,
    dpi: int = 300,
) -> dict:
    width_in, height_in = trim_box(trim)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=(width_in * 72, height_in * 72))
    page_count = 0
    for img_path in page_images:
        c.drawImage(
            ImageReader(str(img_path)),
            0,
            0,
            width=width_in * 72,
            height=height_in * 72,
            preserveAspectRatio=True,
            anchor="c",
        )
        c.showPage()
        page_count += 1
        if single_sided:
            c.showPage()
            page_count += 1
    # KDP paperback minimum is typically 24 pages; pad with blanks if needed
    while page_count < 24:
        c.showPage()
        page_count += 1
    if page_count % 2 == 1:
        c.showPage()
        page_count += 1
    c.save()
    return {
        "pdf": str(out_pdf),
        "page_count": page_count,
        "trim": trim,
        "width_in": width_in,
        "height_in": height_in,
        "dpi": dpi,
        "single_sided": single_sided,
    }


def cover_dimensions(
    page_count: int,
    trim: str = "letter",
    paper: str = "white",
    bleed: bool | None = None,
) -> dict:
    specs = load_specs()
    bleed_in = float(specs["bleed_inches"]) if bleed is not False else float(specs["bleed_inches"])
    # Covers always need bleed on KDP
    bleed_in = float(specs["bleed_inches"])
    width_in, height_in = trim_box(trim)
    spine = spine_width(page_count, paper=paper)
    cover_w = bleed_in + width_in + spine + width_in + bleed_in
    cover_h = bleed_in + height_in + bleed_in
    dpi = int(specs["dpi"])
    return {
        "trim": trim,
        "page_count": page_count,
        "paper": paper,
        "bleed_in": bleed_in,
        "spine_in": round(spine, 4),
        "trim_width_in": width_in,
        "trim_height_in": height_in,
        "cover_width_in": round(cover_w, 4),
        "cover_height_in": round(cover_h, 4),
        "cover_width_px": int(round(cover_w * dpi)),
        "cover_height_px": int(round(cover_h * dpi)),
        "gutter_in": gutter_for_pages(page_count),
        "spine_text_allowed": page_count >= 79,
        "dpi": dpi,
    }
