# Mile Marker

Automated digital-product income stream for **Central Ohio / Columbus** living kits.

Built to be expanded by Cursor: add a product folder, update the catalog, ship.

## Status

- Compliance: **approved** for digital product sales (Bucket E).
- Niche: local living — **not** banking, cybersecurity, or employer-related.
- Model: create once → sell on Gumroad/Etsy forever → Cursor adds SKUs.
- Still off WF systems / work hours.

## Structure

```text
mile-marker/
  site/                 # Marketing site (Vite)
  products/             # Source kits (markdown → PDF/HTML)
  launch/               # Gumroad copy, pricing, checklist
  PRODUCT_FACTORY.md    # How to ask Cursor for the next SKU
```

## Quick start (site)

```bash
cd mile-marker/site
npm install
npm run dev
```

## First three kits

| SKU | Price target | Folder |
| --- | --- | --- |
| Weekend in Columbus — 48-Hour Field Kit | $9 | `products/weekend-columbus` |
| Move to Columbus — Settling Pack | $19 | `products/move-in-pack` |
| Stadium Weekend Logistics Sheet | $7 | `products/stadium-weekend` |

## Launch path

1. Get written Compliance OK for digital product sales.
2. Create Gumroad account; paste copy from `launch/gumroad-copy.md`.
3. Export each product markdown to PDF (browser print or `npx md-to-pdf`).
4. Deploy site to Vercel/Netlify; point CTAs at Gumroad links.
5. Soft-launch on personal LinkedIn/Facebook (no WF systems, no work time).
6. Ask Cursor: “Add the next Mile Marker kit for [niche] using PRODUCT_FACTORY.md”.
