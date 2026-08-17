"""Build KDP-ready interior and cover-dimension helpers."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfgen.pathobject import PDFPathObject

from .specs import gutter_for_pages, load_specs, spine_width, trim_box

_PATH_CMD = re.compile(r"([MCQLZ])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")


def blank_page_png(path: Path, trim: str, dpi: int = 300) -> Path:
    width_in, height_in = trim_box(trim)
    w = int(round(width_in * dpi))
    h = int(round(height_in * dpi))
    Image.new("L", (w, h), 255).save(path, dpi=(dpi, dpi))
    return path


def _svg_path_d(svg_text: str) -> str | None:
    m = re.search(r'<path[^>]*\sd="([^"]+)"', svg_text)
    return m.group(1) if m else None


def _draw_svg_vector_page(
    c: canvas.Canvas,
    svg_path: Path,
    *,
    width_in: float,
    height_in: float,
    dpi: int,
) -> bool:
    """Draw page-*.svg Béziers as true PDF vectors (even-odd fill)."""
    svg = svg_path.read_text(encoding="utf-8")
    d = _svg_path_d(svg)
    if not d:
        return False

    scale = 72.0 / dpi
    page_h_px = height_in * dpi

    def px_to_pt(x: float, y: float) -> tuple[float, float]:
        return x * scale, (page_h_px - y) * scale

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width_in * 72, height_in * 72, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)

    path: PDFPathObject = c.beginPath()
    tokens = _PATH_CMD.findall(d)
    # flatten to alternating commands / numbers
    items: list[str] = []
    for cmd, num in tokens:
        if cmd:
            items.append(cmd)
        else:
            items.append(num)

    i = 0
    cur = (0.0, 0.0)
    while i < len(items):
        op = items[i]
        i += 1
        if op == "M":
            x, y = float(items[i]), float(items[i + 1])
            i += 2
            cur = (x, y)
            path.moveTo(*px_to_pt(x, y))
        elif op == "L":
            x, y = float(items[i]), float(items[i + 1])
            i += 2
            cur = (x, y)
            path.lineTo(*px_to_pt(x, y))
        elif op == "C":
            x1, y1 = float(items[i]), float(items[i + 1])
            x2, y2 = float(items[i + 2]), float(items[i + 3])
            x3, y3 = float(items[i + 4]), float(items[i + 5])
            i += 6
            path.curveTo(*px_to_pt(x1, y1), *px_to_pt(x2, y2), *px_to_pt(x3, y3))
            cur = (x3, y3)
        elif op == "Q":
            # Convert quadratic to cubic for reportlab
            cx, cy = float(items[i]), float(items[i + 1])
            x3, y3 = float(items[i + 2]), float(items[i + 3])
            i += 4
            x0, y0 = cur
            # cubic controls = 2/3 along toward quad control
            x1 = x0 + 2.0 / 3.0 * (cx - x0)
            y1 = y0 + 2.0 / 3.0 * (cy - y0)
            x2 = x3 + 2.0 / 3.0 * (cx - x3)
            y2 = y3 + 2.0 / 3.0 * (cy - y3)
            path.curveTo(*px_to_pt(x1, y1), *px_to_pt(x2, y2), *px_to_pt(x3, y3))
            cur = (x3, y3)
        elif op == "Z":
            path.close()
        else:
            # Unexpected token — abort to raster fallback
            return False

    c.drawPath(path, fill=1, stroke=0, fillMode=1)  # even-odd
    return True


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
    vector_pages = 0
    for img_path in page_images:
        svg_path = img_path.with_suffix(".svg")
        drew = False
        if svg_path.exists():
            drew = _draw_svg_vector_page(
                c, svg_path, width_in=width_in, height_in=height_in, dpi=dpi
            )
            if drew:
                vector_pages += 1
        if not drew:
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
        "vector_pages": vector_pages,
    }


def cover_dimensions(
    page_count: int,
    trim: str = "letter",
    paper: str = "white",
    bleed: bool | None = None,
) -> dict:
    specs = load_specs()
    bleed_in = float(specs["bleed_inches"]) if bleed is not False else float(specs["bleed_inches"])
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
