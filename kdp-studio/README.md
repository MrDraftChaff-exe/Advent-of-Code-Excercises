# KDP Studio

Toolkit for creating **coloring books** and other useful **Amazon Kindle Direct Publishing (KDP)** print-on-demand paperbacks — planners, journals, logbooks, puzzle books, and workbooks.

## Preview everything locally

```bash
cd kdp-studio
./scripts/preview.sh
# → http://127.0.0.1:8765
```

Or: `cd tools && python3 -m kdp_studio preview`

Preview Studio shows pages, cover wrap, listing copy, comparable-price research, and the KDP publish checklist.

## Structure

```text
kdp-studio/
  preview/             # Local Preview Studio UI
  specs/               # Trim sizes, bleed, gutter, print rules
  templates/           # Meta schema + type templates
  tools/kdp_studio/    # CLI
  products/            # One folder per title
  launch/              # Upload checklist + listing copy
  PRODUCT_FACTORY.md   # Prompt for the next SKU
```

## Quick start (build a title)

```bash
cd kdp-studio
python3 -m pip install -r requirements.txt
cd tools

python3 -m kdp_studio new --slug calm-geometry-30 \
  --title "Calm Geometry" \
  --subtitle "30 Easy Patterns to Color" \
  --designs 30

python3 -m kdp_studio pages --slug calm-geometry-30
python3 -m kdp_studio interior --slug calm-geometry-30
python3 -m kdp_studio cover --slug calm-geometry-30 --render
python3 -m kdp_studio validate --slug calm-geometry-30
```

## Pricing from comparable sales

```bash
# Try live Amazon search (often blocked) → falls back to niche demo comps
python3 -m kdp_studio price --slug calm-geometry-30 --apply

# Best for real research: paste comps you gathered into a JSON file
python3 -m kdp_studio price --slug calm-geometry-30 \
  --comps-file ../templates/coloring-book/comps.example.json \
  --apply
```

Strategies: `median` (default), `undercut`, `premium`. Writes `products/<slug>/pricing.json` and can update `list_price_usd`.

## Publish to KDP (important)

**Amazon does not provide a public KDP upload API** for indie paperbacks. Auto-upload tools that click the website are unofficial, brittle, and may conflict with Amazon’s terms.

What KDP Studio does instead:

```bash
python3 -m kdp_studio publish --slug calm-geometry-30
# → products/<slug>/publish/  (interior, cover dims, kdp-fields.json, UPLOAD.md)

python3 -m kdp_studio publish --slug calm-geometry-30 --assist   # dry-run guidance
# --live opens KDP Bookshelf in Playwright for manual paste (experimental)
```

Then upload from [KDP Bookshelf](https://kdp.amazon.com/en_US/bookshelf) using the package fields, or follow [`launch/CHECKLIST.md`](./launch/CHECKLIST.md).

## Products

| SKU | Type | Trim | Price | Status | Folder |
| --- | --- | --- | --- | --- | --- |
| Forest Animals — 30 Woodland Friends | coloring-book | letter | $9.99 | draft | `products/forest-animals-30` |
| Sports — 30 Action Pages | coloring-book | letter | comps | draft | `products/sports-30` |
| Math Adventures — 30 Number & Shape Pages | coloring-book | letter | comps | draft | `products/math-30` |
| Physical Science — 30 Wonder Pages | coloring-book | letter | comps | draft | `products/physical-science-30` |
| Chemistry Lab — 30 Molecule & Flask Pages | coloring-book | letter | comps | draft | `products/chemistry-30` |
| Sea Life — 30 Ocean Friends | coloring-book | letter | comps | draft | `products/sea-life-30` |
| Space Explorers — 30 Cosmic Pages | coloring-book | letter | comps | draft | `products/space-30` |
| Calm Geometry — 30 Easy Patterns | coloring-book | letter | — | draft | `products/calm-geometry-30` |

All new themed books use **AI-assisted line art** (disclose on KDP). Pages are **one clear subject** with thick closed outlines; import runs threshold + morphological close + endpoint bridging. Covers use full-bleed colored heroes with Fredoka/Nunito type on a full wrap (front, spine, back). Rebuild from `art-source/` with:

```bash
python3 scripts/build_theme_book.py sports-30
# covers only (faster):
python3 scripts/build_theme_book.py --covers-only
# also: forest-animals-30 math-30 physical-science-30 chemistry-30 sea-life-30 space-30
```

## Other POD types

| Type | Typical trim | Notes |
| --- | --- | --- |
| `coloring-book` | letter / square | Single-sided; 300 DPI line art |
| `planner` | letter / trade | Dated or undated grids |
| `journal` | trade / a5ish | Lined or prompts |
| `logbook` | trade | Repeatable forms |
| `puzzle` | letter | Include answer key |
| `workbook` | letter | Larger type for kids |

See [`specs/kdp-print-specs.md`](./specs/kdp-print-specs.md) and [`PRODUCT_FACTORY.md`](./PRODUCT_FACTORY.md).
