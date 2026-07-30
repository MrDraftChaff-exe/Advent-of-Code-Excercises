# Launch checklist — Buckeye Trail Guide

## 0) Compliance — APPROVED

- [x] Compliance OK'd digital product sales (Bucket E)
- [ ] Keep the written approval somewhere you can find it
- [ ] Still: no WF laptop, email, Slack, or work hours for this project
- [ ] Still: no banking/cyber/employer content in kits

## 1) Accounts

- [ ] Gumroad (or Payhip / Lemon Squeezy)
- [ ] Personal email (not employer)
- [ ] Optional: Beehiiv/Substack for later waitlist

## 2) Export products to PDF

From each `products/*/product.md`:

```bash
# option A — open in any markdown preview and Print → PDF
# option B — if you install md-to-pdf:
npx --yes md-to-pdf buckeye-trail-guide/products/weekend-columbus/product.md
npx --yes md-to-pdf buckeye-trail-guide/products/move-in-pack/product.md
npx --yes md-to-pdf buckeye-trail-guide/products/stadium-weekend/product.md
```

## 3) Publish with the auto-deploy tool

Preferred (once tokens are in `publisher/.env`):

```bash
cd buckeye-trail-guide/publisher
npm run publish -- --platforms gumroad
# optional:
npm run publish -- --platforms gumroad,etsy,lemonsqueezy
```

Manual fallback: paste copy from `gumroad-copy.md` and upload PDFs in each dashboard.

## 4) Deploy site

```bash
cd buckeye-trail-guide/site
npm run build
# deploy `dist/` to Vercel, Netlify, or Cloudflare Pages
```

- [ ] Custom domain optional (`milemarkerohio.com` or similar)
- [ ] Smoke-test mobile CTA buttons

## 5) Soft launch (personal channels only)

- [ ] 1 Facebook/Nextdoor post: movers + hosts angle  
- [ ] 1 personal LinkedIn post (no WF confidential; no tagging employer)  
- [ ] Offer weekend kit free to 5 friends for testimonials  

## 6) Ask Cursor for SKU #4

Open `PRODUCT_FACTORY.md` and run the prompt (farmers market calendar, Hocking day trip, etc.).

## Success metrics (30 days)

| Signal | Target |
| --- | --- |
| Site visitors | 100+ |
| Sales | 5+ (any SKU) |
| Refunds | 0–1 |
| Next action | Double down on winner OR ship SKU #4 |
