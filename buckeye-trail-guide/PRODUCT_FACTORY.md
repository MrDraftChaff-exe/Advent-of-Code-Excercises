# Product Factory — how Cursor adds the next guide

When you want a new product, paste this prompt into Cursor:

---

Create a new Buckeye Trail Guide digital download.

**Brand:** Buckeye Trail Guide — a collection of guides curated by Clayton Householder, a Columbus Ohio native. Guides will be a variety of subject matter that spans a large domain from personal life to professional and anything that can make life easier.

**Constraints:** Never banking, cybersecurity, Wells Fargo, PAM, or employer topics. Avoid trademarked university/team logos; use generic wording where needed.

**Deliverables:**
1. Create `buckeye-trail-guide/products/<slug>/` with:
   - `product.md` — full customer-facing guide (printable, scannable, checklist-heavy)
   - `meta.json` — title, price, one-liner, bullets, SEO tags, files list
2. Add the product to `buckeye-trail-guide/site/src/catalog.js`
3. Add a Gumroad block to `buckeye-trail-guide/launch/gumroad-copy.md`
4. Keep voice: practical, clear, no hype, no fake stats

**Format rules for product.md:**
- One clear outcome in the title
- 1 short intro paragraph
- Checklists, tables, worksheets
- Fits on printable pages; use markdown headings

**Pricing guide:** single sheet $5–$9 · pack $15–$29 · bundle $39

---

## SKU ideas backlog (pick any)

Personal / local
- Clintonville / German Village walking food crawl planner
- Columbus farmers market seasonal calendar
- First winter in Ohio car + home kit
- Apartment hunting scorecard (Columbus neighborhoods)
- Short North gallery hop evening plan
- ~~Hocking Hills day-trip from Columbus~~ → shipped as `products/hocking-hills-day`
- ~~Top 15 super natural experiences in Columbus under $15~~ → shipped as `products/columbus-nature-15`
- Holiday guest hosting timeline (central Ohio weather aware)

Professional / life admin
- First-job / interview week checklist
- Remote-work day reset guide
- Monthly personal finance reset worksheet (generic, non-advisory)
- Home office setup checklist
- Subscription & bills annual audit sheet
- Travel packing + itinerary template (any city)
