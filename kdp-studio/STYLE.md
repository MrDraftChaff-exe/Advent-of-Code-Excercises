# Quiet Places art style — foundation for ALL KDP Studio coloring art

This is the **only** allowed interior art style for coloring books in this repo.

## Non-negotiables

1. **Style:** Bold & easy cozy illustration — thick-but-not-blobbed closed outlines, large simple shapes, full-frame scenes (landscapes, animals, flowers, mushrooms, cozy objects, simple patterns). Hand-drawn feel. Square 8.5×8.5 when bold/easy.
2. **Never** procedural clip-art, geometric primitives as subjects, sparse icon dumps, or “companion enrichment” junk sprinkled onto scenes.
3. **Never** letters, words, numbers, or readable signage on interior pages. Blank signs may show a heart, flower, or leaf icon only.
4. **Never** solid black fills, gray shading, hatching, or overly dark / marker-blob lines. Medium-bold outline weight; hollow interiors ready to color.
5. **Never** black backgrounds or page frames that flood-fill solid.

## Production path (Quiet Places)

```bash
# 1) Illustrated line scenes as qp-gen-01.png … (no text in the prompt)
# 2) Ink cleanup (medium weight, hollow only true solid fills)
python3 scripts/inkify_quiet_places.py /path/to/qp-gen-dir
# 3) Build (raster page placement — do not re-potrace Quiet Places art)
python3 scripts/build_theme_book.py quiet-places-40
```

Do **not** use procedural geometry generators. Quiet Places pages are placed as cleaned rasters so vector reprocessing cannot shred the lines.

## Future titles

Any new coloring SKU must reuse this style and pipeline. If it would look different after removing the title, it is the wrong style — regenerate.

## Current titles (same style, different subjects)

Quiet Places, Stained Glass, Cars, Planes, Buildings, Food, Mountains — all 40-page square bold-and-easy books. Use `scripts/inkify_bold_easy.py` + `scripts/build_theme_book.py <slug>`.
