# Mile Marker Publisher

Deploy every kit in `../products/` to your sales platforms from one command.

## What it syncs

| Platform | Title/price/desc | Files | Publish URL → site |
| --- | --- | --- | --- |
| **Gumroad** | Yes | Yes (presign → S3 → attach) | Yes (`site/src/catalog.js`) |
| **Etsy** | Yes | Yes (listing file upload) | Listing URL saved in state |
| **Lemon Squeezy** | Yes | **Manual** (API limitation) | State only |

Source of truth: each `products/<id>/meta.json` + files in that folder.

## Setup

```bash
cd mile-marker-publisher/publisher
cp .env.example .env
# paste tokens into .env
npm install
```

### Gumroad token
Gumroad → Settings → Advanced → API. Token needs **edit_products**.

### Etsy
1. Create an app at developers.etsy.com  
2. OAuth for your shop (listings_w, listings_r)  
3. Set `ETSY_SHOP_ID` and a digital `ETSY_TAXONOMY_ID`  
4. Optional: `ETSY_AUTO_PUBLISH=true` to activate after upload  

### Lemon Squeezy
API key + store id. After deploy, attach PDF/xlsx in the LS dashboard when prompted.

## Commands

```bash
# Safe preview
npm run dry-run
npm run publish -- --dry-run --platforms gumroad,etsy,lemonsqueezy

# Live: Gumroad only (recommended first)
npm run publish -- --platforms gumroad

# One product
npm run publish -- --platforms gumroad --product weekend-columbus

# All configured platforms
npm run publish -- --platforms gumroad,etsy,lemonsqueezy

# Only rewrite site CTAs from state.json
npm run publish -- --sync-site-only
```

After a successful Gumroad sync, `state.json` stores product ids/URLs and the site catalog Gumroad links are rewritten automatically.

## Workflow with Cursor

1. Ask Cursor to add/update a kit (`PRODUCT_FACTORY.md`).  
2. Run `npm run publish -- --platforms gumroad,etsy`.  
3. Redeploy the marketing site if needed (`cd ../site && npm run build`).  

No more hand-copying prices/files into each dashboard (except Lemon Squeezy files).

## Security

- Never commit `.env`  
- Use a personal Gumroad/Etsy account (not employer accounts)  
- Keep Compliance constraints: no WF systems/time for publishing
