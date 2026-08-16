"""Normalize external/AI line-art into KDP page PNGs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from .specs import trim_box


def normalize_to_page(
    src: Path,
    out: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> Path:
    width_in, height_in = trim_box(trim)
    canvas_w = int(round(width_in * dpi))
    canvas_h = int(round(height_in * dpi))
    margin = int(round(margin_in * dpi))
    inner = (canvas_w - 2 * margin, canvas_h - 2 * margin)

    im = Image.open(src)
    fitted = ImageOps.contain(im, inner, Image.Resampling.LANCZOS)
    g = ImageEnhance.Contrast(fitted.convert("L")).enhance(1.8)
    g = g.point(lambda p: 255 if p > 230 else (0 if p < 180 else p))

    canvas = Image.new("L", (canvas_w, canvas_h), 255)
    canvas.paste(g, ((canvas_w - g.width) // 2, (canvas_h - g.height) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, dpi=(dpi, dpi))
    return out


def import_art_folder(
    art_dir: Path,
    pages_dir: Path,
    *,
    trim: str = "letter",
    dpi: int = 300,
    margin_in: float = 0.5,
) -> list[Path]:
    files = sorted(art_dir.glob("*.png")) + sorted(art_dir.glob("*.jpg"))
    if not files:
        raise FileNotFoundError(f"No images in {art_dir}")
    paths: list[Path] = []
    pages_dir.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(files, start=1):
        out = pages_dir / f"page-{i:02d}.png"
        normalize_to_page(src, out, trim=trim, dpi=dpi, margin_in=margin_in)
        paths.append(out)
    return paths
