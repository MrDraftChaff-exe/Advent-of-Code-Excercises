# KDP upload checklist

Use once interior.pdf validates and cover art is ready.

## Before upload

- [ ] `python3 -m kdp_studio validate --slug <slug>` → OK
- [ ] Trim in meta matches KDP paperback trim selection
- [ ] Interior page count matches cover spine calculation
- [ ] Single-sided coloring: blank page after each design
- [ ] No trademarks / celebrity likenesses / copyrighted characters
- [ ] AI disclosure decided (`meta.ai_assisted`) and ready to declare
- [ ] Title + subtitle ≤ Amazon field limits; readable as thumbnail
- [ ] 7 backend keywords researched (no stuffing competitor ASIN text)
- [ ] Two browse categories chosen
- [ ] Price set; royalty plan chosen (standard vs expanded)

## Files to upload

| Asset | Source |
| --- | --- |
| Manuscript (interior) | `products/<slug>/interior.pdf` |
| Cover | Full wrap PDF/PNG sized from `products/<slug>/cover/dimensions.json` |
| Listing copy | `launch/listings/<slug>.md` |

## After live

- [ ] Order author copy / proof
- [ ] Check print: line weight, margins, cover crop
- [ ] Set `meta.status` to `live`
- [ ] Note ASIN in meta or listing file
- [ ] Soft-launch posts (optional social)

## Compliance notes

- This toolkit does **not** upload to Amazon for you; publish from your KDP account.
- Keep personal tax/banking info out of the repo.
- Prefer original geometric or commissioned art over ambiguous “inspired by” IP.
