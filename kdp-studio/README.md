# KDP Studio

Toolkit for creating **coloring books** and other useful **Amazon Kindle Direct Publishing (KDP)** print-on-demand paperbacks — planners, journals, logbooks, puzzle books, and workbooks.

Built to be expanded by Cursor: scaffold a SKU, generate or drop in pages, build a print-ready interior PDF, compute cover wrap size, validate, then upload in KDP.

## Structure

```text
kdp-studio/
  specs/               # Trim sizes, bleed, gutter, print rules
  templates/           # Meta schema + type templates
  tools/kdp_studio/    # CLI: new → pages → interior → cover → validate
  products/            # One folder per title
  launch/              # Upload checklist + listing copy
  PRODUCT_FACTORY.md   # Prompt for the next SKU
```

## Quick start

```bash
cd kdp-studio
python3 -m pip install -r requirements.txt
cd tools

# Scaffold + generate first sample title
python3 -m kdp_studio new --slug calm-geometry-30 \
  --title "Calm Geometry" \
  --subtitle "30 Easy Patterns to Color" \
  --designs 30

python3 -m kdp_studio pages --slug calm-geometry-30
python3 -m kdp_studio interior --slug calm-geometry-30
python3 -m kdp_studio cover --slug calm-geometry-30
python3 -m kdp_studio validate --slug calm-geometry-30
```

Outputs land in `products/calm-geometry-30/` (`pages/`, `interior.pdf`, `cover/dimensions.json`).

## Products

| SKU | Type | Trim | Status | Folder |
| --- | --- | --- | --- | --- |
| Calm Geometry — 30 Easy Patterns | coloring-book | letter | draft | `products/calm-geometry-30` |

## Other POD types

Use the same pipeline; change `--type` and art source:

| Type | Typical trim | Notes |
| --- | --- | --- |
| `coloring-book` | letter / square | Single-sided; 300 DPI line art |
| `planner` | letter / trade | Dated or undated grids |
| `journal` | trade / a5ish | Lined or prompts |
| `logbook` | trade | Repeatable forms |
| `puzzle` | letter | Include answer key |
| `workbook` | letter | Larger type for kids |

See [`specs/kdp-print-specs.md`](./specs/kdp-print-specs.md) and [`PRODUCT_FACTORY.md`](./PRODUCT_FACTORY.md).

## Upload

This repo builds files; you publish from your KDP account. Follow [`launch/CHECKLIST.md`](./launch/CHECKLIST.md).
