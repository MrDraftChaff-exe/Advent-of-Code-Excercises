# Buckeye Trail Guide

Deploy every kit in `../products/` to your sales platforms from one command.

## What it syncs

| Platform | Title/price/desc | Files | Publish URL → site |
| --- | --- | --- | --- |
| **Gumroad** | Yes | Yes (presign → S3 → attach) | Yes (`site/src/catalog.js`) |
| **Lemon Squeezy** | Yes | **Manual** (API limitation) | State only |
| **Etsy** | — | — | **Paused** (fees) — code kept, not in pipeline |

Source of truth: each `products/<id>/meta.json` + files in that folder.

## Setup

```bash
cd buckeye-trail-guide/publisher
cp .env.example .env
npm install
```

### Gumroad (primary)

Gumroad → Settings → Advanced → API (`edit_products`). Then:

```bash
npm run publish -- --platforms gumroad
```

### Lemon Squeezy (optional)

See `.env.example` for `LEMON_SQUEEZY_*` keys.

```bash
npm run publish -- --platforms lemonsqueezy
```

### Etsy — paused

Not in the active pipeline. See **[ETSY_SETUP.md](./ETSY_SETUP.md)**.

### Dry run / site only

```bash
npm run dry-run
npm run publish -- --sync-site-only
```

## Workflow with Cursor

1. Ask Cursor to add/update a kit (`PRODUCT_FACTORY.md`).  
2. `npm run publish -- --platforms gumroad`  
3. Redeploy marketing site if needed (`cd ../site && npm run build`).  

## Security

- Never commit `.env`  
- Never paste API secrets/tokens into chat  
- Personal Gumroad account only; no WF systems/time  
