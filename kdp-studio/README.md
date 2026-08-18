# KDP Studio

Bold & easy KDP coloring books in the **Quiet Places** art foundation ([`STYLE.md`](./STYLE.md)).

## Products

| SKU | Trim | Folder |
| --- | --- | --- |
| Quiet Places — 40 Bold & Easy Designs | square | `products/quiet-places-40` |
| Stained Glass — 40 Bold & Easy Designs | square | `products/stained-glass-40` |
| Cars — 40 Bold & Easy Designs | square | `products/cars-40` |
| Planes — 40 Bold & Easy Designs | square | `products/planes-40` |
| Buildings — 40 Bold & Easy Designs | square | `products/buildings-40` |
| Food — 40 Bold & Easy Designs | square | `products/food-40` |
| Mountains — 40 Bold & Easy Designs | square | `products/mountains-40` |

## Build

```bash
# After illustrated gens exist under /tmp/gen/<theme>/:
python3 scripts/inkify_bold_easy.py --slug stained-glass-40 --src /tmp/gen/stained-glass --glob 'sg-gen-*.png' --out-prefix sg2
python3 scripts/build_theme_book.py stained-glass-40

# Or all registered themes:
python3 scripts/build_theme_book.py --all
```

Pen name: **Elsie Wren**. Disclose AI-assisted art on the KDP form (not on the printed wrap).

Do **not** buy a barcode. Each wrap already has an empty 2.0" × 1.2" well; KDP prints a free EAN-13. A free KDP ISBN is enough for Amazon-only paperbacks.
