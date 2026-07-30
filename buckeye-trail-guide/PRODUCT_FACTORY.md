# Product Factory — how Cursor adds the next guide

When you want a new product, paste this prompt into Cursor:

---

Create a new Buckeye Trail Guide digital download.

**Brand:** Buckeye Trail Guide — printable guides curated by Keith Householder, a Columbus Ohio native. Topics span personal life, local know-how, settling in, planning, and everyday admin — whatever helps you get the next thing done with less friction.

**Constraints:** Never banking, cybersecurity, Wells Fargo, PAM, or employer topics. Avoid trademarked university/team logos; use generic wording where needed.

**Deliverables:**
1. Create `buckeye-trail-guide/products/<slug>/` with:
   - `product.md` — full customer-facing guide (printable, scannable, checklist-heavy)
   - `meta.json` — title, price, one-liner, bullets, SEO tags, files list
   - `cover.png` — topic-derived cover (see Thumbnail / cover rules)
2. Add the product to `buckeye-trail-guide/site/src/catalog.js`
3. Add a Gumroad block to `buckeye-trail-guide/launch/gumroad-copy.md`
4. Generate unique topic thumbnail + cover assets (see rules below)
5. Keep voice: practical, clear, no hype, no fake stats

**Format rules for product.md:**
- One clear outcome in the title
- 1 short intro paragraph
- Checklists, tables, worksheets
- Fits on printable pages; use markdown headings
- End with brand line + affiliation disclaimer:  
  `*Buckeye Trail Guide · Curated by Keith Householder · Columbus, Ohio*`  
  `*Personal use. Not affiliated with The Ohio State University or the City of Columbus.*`  
  (Add product-specific park/org notes on the same disclaimer line when relevant.)

**Thumbnail / cover rules (required):**
- Every SKU must have a **unique** image set derived from **that guide’s topic** (what the customer is buying), not the brand mascot and not a reused photo from another SKU.
- Do **not** use the cat badge / trail emblem as the product thumbnail or cover.
- Create:
  - `brand/covers/<slug>.png` + `site/public/covers/<slug>.png` + `products/<slug>/cover.png` (wide cover)
  - `brand/thumbnails/<slug>.png` + `site/public/thumbnails/<slug>.png` (square 1024×1024 shop card)
- Thumbnail layout: topic photo on top + dark text bar with `BUCKEYE TRAIL GUIDE` / title / subtitle.
- No trademarked team/university logos in imagery.
- After generating, upload the square thumbnail to Gumroad for that product (API or dashboard).

**Pricing guide:** every product **under $10** (typical $5–$9). Prefer simple single-price digital downloads over premium packs.

---

## SKU ideas backlog (pick any)

Personal / local
- Clintonville / German Village walking food crawl planner
- Columbus farmers market seasonal calendar
- First winter in Ohio car + home kit
- Apartment hunting scorecard (Columbus neighborhoods)
- Short North gallery hop evening plan
- ~~Hocking Hills day-trip from Columbus~~ → shipped as `products/hocking-hills-day`
- ~~Top 15 super natural experiences in Columbus under $15~~ → shipped as `products/columbus-nature-15` (nature)
- ~~Columbus supernatural / paranormal under $30~~ → shipped as `products/columbus-supernatural` ($2 guide)
- ~~Top 30 fishing spots around Columbus~~ → shipped as `products/columbus-fishing-30`
- Holiday guest hosting timeline (central Ohio weather aware)

Professional / life admin
- First-job / interview week checklist
- Remote-work day reset guide
- Monthly personal finance reset worksheet (generic, non-advisory)
- Home office setup checklist
- Subscription & bills annual audit sheet
- Travel packing + itinerary template (any city)
