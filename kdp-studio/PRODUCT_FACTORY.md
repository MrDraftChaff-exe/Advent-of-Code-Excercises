# Product Factory — next KDP / coloring-book SKU

Paste this into Cursor when you want a new print-on-demand title.

---

Create a new **KDP Studio** product.

**Mandatory art style:** Follow [`STYLE.md`](./STYLE.md) exactly. The Quiet Places bold-and-easy look is the **only** allowed coloring-book interior style. Never procedural geometry, never letters/words on pages, never solid black fills or overly dark blob lines.

**Imprint:** Coloring books and other useful POD (planners, journals, logbooks). Original art and copy only.

**Defaults for coloring books:**
- Trim: `square` (8.5×8.5) for bold & easy; `letter` only if STYLE.md still fits
- No interior bleed (art inside ~0.5" margin)
- Single-sided (design + blank)
- 300 DPI black line art via `scripts/inkify_quiet_places.py`
- White paper, black ink, matte cover
- List price often $7.99–$12.99
- Pen name: Elsie Wren

**Deliverables:**
1. Scaffold under `products/<slug>/` with `art-source/`, `pages/`, `cover/`, `meta.json`, `brief.md`
2. Generate illustrated scenes with **no text** in the image; inkify; build with `scripts/build_theme_book.py` (extend THEMES only for same-style titles)
3. Listing in `launch/listings/<slug>.md`
4. Update `README.md` product table
5. `status: ready` only when interior PDF + cover exist

**Quality bar:**
- Matches Quiet Places sample pages (cozy full scenes, medium-bold outlines)
- No readable text on interiors
- Black ink density roughly ≤14.5% after inkify
- Cover title readable as an Amazon thumbnail
- If AI art is used, `ai_assisted: true` + KDP disclosure

**Anti-redundancy:** Do not resurrect deleted theme books (forest, sports, math, chemistry, sea, space). New titles must be new subjects in the same style.
