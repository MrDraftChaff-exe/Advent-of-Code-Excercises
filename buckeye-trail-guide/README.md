# Buckeye Trail Guide

A collection of guides curated by **Clayton Householder**, a Columbus Ohio native. Guides will be a variety of subject matter that spans a large domain from personal life to professional and anything that can make life easier.

Built to be expanded by Cursor: add a product folder, update the catalog, ship.

## Status

- Compliance: **approved** for digital product sales (Bucket E).
- Model: create once → sell on Gumroad/Etsy forever → Cursor adds SKUs.
- Still off WF systems / work hours.
- Not affiliated with The Ohio State University.

## Structure

```text
buckeye-trail-guide/
  brand/                # Mascot icon + favicons
  site/                 # Marketing site (Vite)
  products/             # Source guides (markdown → PDF/HTML)
  launch/               # Gumroad copy, pricing, checklist
  PRODUCT_FACTORY.md    # How to ask Cursor for the next SKU
```

## Quick start (site)

```bash
cd buckeye-trail-guide/site
npm install
npm run dev
```

## Guides

| SKU | Price | Folder | Gumroad |
| --- | --- | --- | --- |
| Weekend in Columbus — 48-Hour Field Kit | $9 | `products/weekend-columbus` | [live](https://buckeyetrailguide.gumroad.com/l/weekend-columbus) |
| Move to Columbus — Settling Pack + Spreadsheet | $24 | `products/move-in-pack` | [live](https://buckeyetrailguide.gumroad.com/l/move-to-columbus) |
| Stadium Weekend Logistics Sheet | $7 | `products/stadium-weekend` | [live](https://buckeyetrailguide.gumroad.com/l/stadium-weekend) |
| Hocking Hills Day Trip — From Columbus | $8 | `products/hocking-hills-day` | [live](https://buckeyetrailguide.gumroad.com/l/hocking-hills-day) |
| Top 15 Super Natural Experiences in Columbus — Under $15 Each | $9 | `products/columbus-nature-15` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-nature-15) |
| Columbus Supernatural / Paranormal Experiences — Under $30 Each | $2 | `products/columbus-supernatural` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-supernatural) |

## Publisher (auto-deploy)

```bash
cd buckeye-trail-guide/publisher
cp .env.example .env   # add tokens
npm install
npm run dry-run
npm run publish -- --platforms gumroad
```

**Etsy:** follow [`publisher/ETSY_SETUP.md`](./publisher/ETSY_SETUP.md) then:

```bash
node src/etsy-auth.js
npm run publish -- --platforms etsy
```

See [`publisher/README.md`](./publisher/README.md).

## This agent session

Continuing from [side-hustle research](https://cursor.com/agents/bc-6df4d7d7-430e-4f20-802e-effeddeb8678) as **Buckeye Trail Guide**.

Next actions for the owner: publish SKU #4 on Gumroad, deploy `site/`, soft-launch posts in `launch/soft-launch-posts.md`, then Etsy when keys are ready.
