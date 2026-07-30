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
npm install
```

### Gumroad
Gumroad → Settings → Advanced → API (`edit_products`). Then:

```bash
npm run publish -- --platforms gumroad
```

### Etsy
Full walkthrough: **[ETSY_SETUP.md](./ETSY_SETUP.md)**

```bash
# put ETSY_API_KEY=keystring:shared_secret in .env (never in chat)
npm run etsy-auth
npm run publish -- --platforms etsy
```

### Both

```bash
npm run publish -- --platforms gumroad,etsy
```

### Dry run / site only

```bash
npm run dry-run
npm run publish -- --sync-site-only
```

## Workflow with Cursor

1. Ask Cursor to add/update a kit (`PRODUCT_FACTORY.md`).  
2. `npm run publish -- --platforms gumroad,etsy`  
3. Redeploy marketing site if needed (`cd ../site && npm run build`).  

## Security

- Never commit `.env`  
- Never paste API secrets/tokens into chat  
- Personal Gumroad/Etsy accounts only; no WF systems/time  
