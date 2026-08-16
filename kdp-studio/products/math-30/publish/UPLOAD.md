# Upload checklist — Math Adventures

Amazon KDP does **not** provide a public API for paperback uploads.
Use this package in [KDP Bookshelf](https://kdp.amazon.com/en_US/bookshelf).

## Steps
1. Create paperback → paste title / subtitle / description from `kdp-fields.json`
2. Keywords + categories from the same file
3. Disclose AI content if `ai_assisted` is true
4. Upload `interior.pdf` as manuscript
5. Upload final cover wrap sized per `cover/dimensions.json`
6. Set list price to **$10.99** (from comps research if run)
7. Proof in KDP Previewer, then publish

## Optional assist
```bash
python3 -m kdp_studio publish --slug math-30 --assist
```
Dry-run opens a guided checklist browser page. `--live` is experimental.
