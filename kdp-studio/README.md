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
| Fantasy — 40 Bold & Easy Designs | square | `products/fantasy-40` |
| Princess Dresses — 40 Bold & Easy Designs | square | `products/dresses-40` |
| Cryptids — 40 North American Legends | square | `products/cryptids-40` |
| Yokai — 40 Japanese Folklore Friends | square | `products/yokai-40` |
| World Cryptids — 40 Global Legends | square | `products/world-cryptids-40` |
| Construction — 40 Bold & Easy Designs | square | `products/construction-40` |
| Mushrooms — 40 Bold & Easy Designs | square | `products/mushrooms-40` |
| Botanicals — 40 Bold & Easy Floral Designs | square | `products/botanicals-40` |
| Celestial Mandalas — 40 Moon and Bloom Wreaths | square | `products/celestial-40` |
| Cottagecore — 40 Cozy Country Scenes | square | `products/cottagecore-40` |
| Cozy Critters — 40 Animals with Personality | square | `products/cozy-critters-40` |
| Dragons — 40 Mythical Friends | square | `products/dragons-40` |
| Spooky Cute — 40 Cozy Halloween Friends | square | `products/spooky-cute-40` |
| Holidays — 40 Seasonal Scenes | square | `products/holidays-40` |
| Chapel Gardens — 40 Peaceful Sunday Scenes | square | `products/chapel-gardens-40` |
| Slow Mornings — 40 Self-Care Scenes | square | `products/slow-mornings-40` |
| Moon Magic — 40 Witchy Night Scenes | square | `products/moon-magic-40` |
| Dark Academia — 40 Gothic Study Scenes | square | `products/dark-academia-40` |
| Corgis — 40 Pembroke Days | square | `products/corgis-40` |
| Zen Gardens — 40 Japanese Garden Scenes | square | `products/zen-gardens-40` |
| Retro Days — 40 Vintage Scenes | square | `products/retro-40` |
| Rest Easy — 40 Calming Scenes | square | `products/rest-easy-40` |
| Dinosaurs — 40 Prehistoric Friends | square | `products/dinosaurs-40` |
| Star Signs — 40 Zodiac Nights | square | `products/star-signs-40` |

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
