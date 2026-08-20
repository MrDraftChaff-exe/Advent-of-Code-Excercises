# Upload checklist — Buildings

Amazon KDP does **not** provide a public API for paperback uploads.
Use this package in [KDP Bookshelf](https://kdp.amazon.com/en_US/bookshelf).

## Fastest path

```bash
./scripts/upload-buildings.sh
```

Or in Preview Studio → Publish → **Stage upload kit**.

Stages `products/buildings-40/upload-kit/` with numbered files + paste-ready fields.

## Steps
1. Create paperback → paste title / subtitle / description from `kdp-fields.json`
2. Keywords + categories from the same file
3. Disclose AI content if `ai_assisted` is true
4. Upload `interior.pdf` as manuscript
5. Upload final cover wrap sized per `cover/dimensions.json`
   - Do **not** buy or paste a barcode. Leave the white well empty; KDP prints a free EAN-13.
   - Choose a **free KDP ISBN** unless you already own an ISBN you want to use.
   - Disclose AI-assisted art in the KDP form (not as printed cover text).
6. Set list price to **$10.99** (from comps research if run)
7. Proof in KDP Previewer, then publish

## Optional assist
```bash
python3 -m kdp_studio publish --slug buildings-40 --assist
```
Dry-run opens a guided checklist browser page. `--live` is experimental.
