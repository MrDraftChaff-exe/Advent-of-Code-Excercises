# Mile Marker Publisher

Automated digital-product income stream for **Central Ohio / Columbus** living kits.

Built to be expanded by Cursor: add a product folder, update the catalog, ship.

## Status

- Compliance: **approved** for digital product sales (Bucket E).
- Niche: local living — **not** banking, cybersecurity, or employer-related.
- Model: create once → sell on Gumroad/Etsy forever → Cursor adds SKUs.
- Still off WF systems / work hours.

## Structure

```text
mile-marker-publisher/
  site/                 # Marketing site (Vite)
  products/             # Source kits (markdown → PDF/HTML)
  launch/               # Gumroad copy, pricing, checklist
  PRODUCT_FACTORY.md    # How to ask Cursor for the next SKU
```

## Quick start (site)

```bash
cd mile-marker-publisher/site
npm install
npm run dev
```

## First three kits

| SKU | Price target | Folder |
| --- | --- | --- |
| Weekend in Columbus — 48-Hour Field Kit | $9 | `products/weekend-columbus` |
| Move to Columbus — Settling Pack + Spreadsheet | $24 | `products/move-in-pack` |
| Stadium Weekend Logistics Sheet | $7 | `products/stadium-weekend` |

## Publisher (auto-deploy)

Deploy all kits to Gumroad / Etsy / Lemon Squeezy from one CLI:

```bash
cd mile-marker-publisher/publisher
cp .env.example .env   # add tokens
npm install
npm run dry-run
npm run publish -- --platforms gumroad
```

See [`publisher/README.md`](./publisher/README.md).
