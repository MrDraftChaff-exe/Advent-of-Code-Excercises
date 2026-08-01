# Launch checklist — Buckeye Trail Guide

## 0) Compliance — APPROVED

- [x] Compliance OK'd digital product sales (Bucket E)
- [ ] Keep the written approval somewhere you can find it
- [ ] Still: no WF laptop, email, Slack, or work hours for this project
- [ ] Still: no banking/cyber/employer content in kits

## 1) Accounts

- [x] Gumroad (`buckeyetrailguide` / businesshouseholder@gmail.com)
- [x] Personal email (not employer)
- [x] Gumroad shop URL renamed to `buckeyetrailguide`
- [ ] Optional: Beehiiv/Substack for later waitlist
- [ ] Etsy shop + API keys — **paused** (fees; see `publisher/ETSY_SETUP.md`)
- [ ] Pinterest Business + developer app (see `publisher/PINTEREST_SETUP.md`) — paused
- [ ] Facebook Page + Page token (see `publisher/FACEBOOK_SETUP.md`)

## 1b) Brand / profile pictures

Upload from `buckeye-trail-guide/brand/profiles/` (no white dead space):

- [ ] Gumroad profile / shop avatar → upload `brand/profiles/gumroad-avatar.png` in Settings → Profile (API cannot set this)
- [x] Gumroad product thumbnails + covers uploaded for all live SKUs (topic-derived)
- [x] Re-upload **topic-derived** square thumbnails for all live SKUs from `brand/thumbnails/<slug>.png`
- [ ] Soft-launch posts → attach `profiles/social-avatar.png`
- ~~Etsy shop icon~~ — paused with Etsy pipeline

## 2) Export products to PDF

PDFs already exist under each `products/*/product.pdf`. Re-export after edits:

```bash
npx --yes md-to-pdf buckeye-trail-guide/products/<slug>/product.md
```

## 3) Publish with the auto-deploy tool

Preferred (once tokens are in `publisher/.env`):

```bash
cd buckeye-trail-guide/publisher
npm run publish -- --platforms gumroad
# optional later:
# npm run publish -- --platforms gumroad,lemonsqueezy
```

Manual fallback: paste copy from `gumroad-copy.md` and upload PDFs in each dashboard.

### Live on Gumroad

- [x] Weekend in Columbus — $4.99
- [x] Move to Columbus — $4.49
- [x] Stadium Weekend — $3.99
- [x] Hocking Hills Day Trip — $3.49
- [x] Outdoor Columbus — 15 Experiences Under $15 Each — $2.99
- [x] Columbus Supernatural / Paranormal Experiences — Under $30 Each — $1.49
- [x] Fishing Near Columbus — 30 Spots with Species & Bait — $3.79
- [x] Columbus Roads: Top 20 to Avoid + Top 20 to Use — Free
- [x] Who to Call — Columbus One-Pager — Free
- [x] First Winter in Central Ohio Checklist — Free
- [x] Farmers Market Seasonal Calendar — Free
- [x] Subscription & Bills Annual Audit — Free
- [x] Recycling & Bulk Trash Cheat Sheet — Free
- [x] COTA / First-Week Transit Card — Free
- [x] Metro Parks Starter Card — Free
- [x] Apartment Walkthrough Photo Checklist — Free
- [x] Pet Weekend / Vet & Boarding Planner — Free
- [x] Holiday Lights Drive Loop — Free

## 4) Deploy site

```bash
cd buckeye-trail-guide/site
npm run build
# deploy `dist/` to Vercel, Netlify, or Cloudflare Pages
```

- [ ] Host marketing site (Vercel/Netlify/Cloudflare)
- [ ] Custom domain optional (e.g. `buckeyetrailguide.com`)
- [ ] Smoke-test mobile CTA buttons
- [ ] Point catalog Gumroad links at live listings after SKU #4 publish

## 5) Soft launch (personal channels only)

- [ ] 1 Facebook/Nextdoor post: movers + hosts angle  
- [ ] 1 personal LinkedIn post (no WF confidential; no tagging employer)  
- [ ] Offer weekend kit free to 5 friends for testimonials  
- [ ] Run 30-day Page calendar (2/day) — `launch/facebook/CALENDAR-30D.md`  
  - `npm run facebook-schedule -- --date YYYY-MM-DD`

## 6) Next SKUs

SKU #4 (Hocking Hills) is in the repo. For #5+, open `PRODUCT_FACTORY.md` and run the prompt.

## Success metrics (30 days)

| Signal | Target |
| --- | --- |
| Site visitors | 100+ |
| Sales | 5+ (any SKU) |
| Refunds | 0–1 |
| Next action | Double down on winner OR ship next SKU |
