# Buckeye Trail Guide — Compliance approved

Digital product stream (Bucket E) is **cleared to launch**. Consulting/gigs still off-limits unless newly approved.

## Brand

**Buckeye Trail Guide** — a collection of guides curated by Keith Householder, a Columbus, Ohio native. Guides span personal life, professional life, and anything that can make life easier.

## What exists now

| Guide | Price | Path |
| --- | --- | --- |
| Weekend in Columbus | $9 | `buckeye-trail-guide/products/weekend-columbus` |
| Move to Columbus Settling Pack + Spreadsheet | $24 | `buckeye-trail-guide/products/move-in-pack` |
| Stadium Weekend Logistics | $7 | `buckeye-trail-guide/products/stadium-weekend` |

Site: `buckeye-trail-guide/site` · Factory: `PRODUCT_FACTORY.md` · Launch: `launch/CHECKLIST.md`

## Launch / sync

```bash
cd buckeye-trail-guide/publisher
npm run publish -- --platforms gumroad
# later: npm run publish -- --platforms gumroad,etsy
```
