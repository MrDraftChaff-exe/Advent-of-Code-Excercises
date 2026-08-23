# Product Factory — how Cursor adds the next guide

When you want a new product, paste this prompt into Cursor:

---

Create a new Buckeye Trail Guide digital download.

**Brand:** Buckeye Trail Guide — printable guides curated by Keith Householder, a Columbus, Ohio native. Topics span personal life, local know-how, settling in, planning, and everyday admin — whatever helps you get the next thing done with less friction.

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

**Pricing guide:** every product **under $10** (typical under $5 for paid; free/$0 allowed for lead magnets). Prefer simple single-price digital downloads over premium packs.

**Anti-redundancy (always):**
Before proposing or shipping any new SKU (free or paid), read live `products/*/product.md` + `meta.json` and reject ideas that mostly duplicate an existing guide’s job (same decision, same checklist, thinner version of a paid pack). Complementary lead magnets are fine (narrower card that points into a paid suite). When listing candidates, call out drops explicitly.

---

## SKU ideas backlog (pick any)

Personal / local
- Clintonville / German Village walking food crawl planner
- ~~Columbus farmers market seasonal calendar~~ → shipped free as `products/farmers-market-calendar`
- ~~First winter in Ohio car + home kit~~ → shipped free as `products/first-winter-ohio`
- Apartment hunting scorecard (Columbus neighborhoods)
- Short North gallery hop evening plan
- ~~Hocking Hills day-trip from Columbus~~ → shipped as `products/hocking-hills-day`
- ~~Outdoor Columbus — 15 experiences under $15~~ → shipped as `products/columbus-nature-15`
- ~~Columbus supernatural / paranormal under $30~~ → shipped as `products/columbus-supernatural` ($2 guide)
- ~~Fishing Near Columbus — 30 spots~~ → shipped as `products/columbus-fishing-30`
- ~~Top 20 roads to avoid + top 20 to use (Columbus)~~ → shipped as `products/columbus-roads-40` (free)
- ~~Who to Call Columbus one-pager~~ → shipped free as `products/columbus-who-to-call`
- ~~Subscription & bills annual audit~~ → shipped free as `products/subscription-bills-audit`
- ~~Recycling & bulk trash cheat sheet~~ → shipped free as `products/recycling-bulk-trash`
- ~~COTA / first-week transit card~~ → shipped free as `products/cota-transit-card`
- ~~Metro Parks starter card~~ → shipped free as `products/metro-parks-starter`
- ~~Apartment walkthrough photo checklist~~ → shipped free as `products/apartment-walkthrough`
- ~~Pet weekend / vet & boarding planner~~ → shipped free as `products/pet-weekend-planner`
- ~~Holiday lights drive loop~~ → shipped free as `products/holiday-lights-loop`
- Holiday guest hosting timeline (central Ohio weather aware)

Professional / life admin
- First-job / interview week checklist
- Remote-work day reset guide
- ~~Monthly personal finance reset worksheet (generic, non-advisory)~~ → related free SKU: `subscription-bills-audit`
- Home office setup checklist
- Travel packing + itinerary template (any city)
