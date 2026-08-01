# Buckeye Trail Guide

Printable guides curated by **Keith Householder**, a Columbus, Ohio native. Topics span personal life, local know-how, settling in, planning, and everyday admin — whatever helps you get the next thing done with less friction.

Built to be expanded by Cursor: add a product folder, update the catalog, ship.

## Status

- Compliance: **approved** for digital product sales (Bucket E).
- Model: create once → sell on Gumroad forever → Cursor adds SKUs.
- Still off WF systems / work hours.
- Etsy: **paused** (platform fees).

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
| Weekend in Columbus — 48-Hour Field Kit | $4.99 | `products/weekend-columbus` | [live](https://buckeyetrailguide.gumroad.com/l/weekend-columbus) |
| Move to Columbus — Settling Pack + Spreadsheet | $4.49 | `products/move-in-pack` | [live](https://buckeyetrailguide.gumroad.com/l/move-to-columbus) |
| Stadium Weekend Logistics Sheet | $3.99 | `products/stadium-weekend` | [live](https://buckeyetrailguide.gumroad.com/l/stadium-weekend) |
| Hocking Hills Day Trip — From Columbus | $3.49 | `products/hocking-hills-day` | [live](https://buckeyetrailguide.gumroad.com/l/hocking-hills-day) |
| Top 15 Super Natural Experiences in Columbus — Under $15 Each | $2.99 | `products/columbus-nature-15` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-nature-15) |
| Columbus Supernatural / Paranormal Experiences — Under $30 Each | $1.49 | `products/columbus-supernatural` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-supernatural) |
| Top 30 Fishing Spots Around Columbus, Ohio | $3.79 | `products/columbus-fishing-30` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-fishing-30) |
| Columbus Roads: Top 20 to Avoid + Top 20 to Use | Free | `products/columbus-roads-40` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-roads-40) |
| Who to Call — Columbus One-Pager | Free | `products/columbus-who-to-call` | [live](https://buckeyetrailguide.gumroad.com/l/columbus-who-to-call) |
| First Winter in Central Ohio Checklist | Free | `products/first-winter-ohio` | [live](https://buckeyetrailguide.gumroad.com/l/first-winter-ohio) |
| Central Ohio Farmers Market Seasonal Calendar | Free | `products/farmers-market-calendar` | [live](https://buckeyetrailguide.gumroad.com/l/farmers-market-calendar) |
| Subscription & Bills Annual Audit Sheet | Free | `products/subscription-bills-audit` | [live](https://buckeyetrailguide.gumroad.com/l/subscription-bills-audit) |
| Recycling & Bulk Trash Cheat Sheet | Free | `products/recycling-bulk-trash` | [live](https://buckeyetrailguide.gumroad.com/l/recycling-bulk-trash) |
| COTA / First-Week Transit Card | Free | `products/cota-transit-card` | [live](https://buckeyetrailguide.gumroad.com/l/cota-transit-card) |
| Metro Parks Starter Card | Free | `products/metro-parks-starter` | [live](https://buckeyetrailguide.gumroad.com/l/metro-parks-starter) |
| Apartment Walkthrough Photo Checklist | Free | `products/apartment-walkthrough` | [live](https://buckeyetrailguide.gumroad.com/l/apartment-walkthrough) |
| Pet Weekend / Vet & Boarding Planner | Free | `products/pet-weekend-planner` | [live](https://buckeyetrailguide.gumroad.com/l/pet-weekend-planner) |
| Holiday Lights Drive Loop | Free | `products/holiday-lights-loop` | [live](https://buckeyetrailguide.gumroad.com/l/holiday-lights-loop) |

## Publisher (auto-deploy)

```bash
cd buckeye-trail-guide/publisher
cp .env.example .env   # add tokens
npm install
npm run dry-run
npm run publish -- --platforms gumroad
```

**Etsy:** paused — see [`publisher/ETSY_SETUP.md`](./publisher/ETSY_SETUP.md) (not in active pipeline).

See [`publisher/README.md`](./publisher/README.md).

## This agent session

Continuing from [side-hustle research](https://cursor.com/agents/bc-6df4d7d7-430e-4f20-802e-effeddeb8678) as **Buckeye Trail Guide**.

Next actions for the owner: deploy `site/`, soft-launch posts in `launch/soft-launch-posts.md`, finish Facebook Page auth at home.
