# Product Factory — next KDP / coloring-book SKU

Paste this into Cursor when you want a new print-on-demand title.

---

Create a new **KDP Studio** product (Kindle Direct Publishing paperback).

**Imprint goal:** Coloring books and other useful print-on-demand items (planners, journals, logbooks, puzzle books, workbooks). Original art and copy only — no trademarked characters, logos, or scraped books.

**Defaults for coloring books:**
- Trim: `letter` (8.5×11) unless kids/bold-easy → `square` (8.5×8.5)
- No interior bleed (art inside ~0.5" margin)
- Single-sided (design + blank)
- 300 DPI black line art
- White paper, black ink, matte cover
- List price often $7.99–$12.99

**Deliverables:**
1. Scaffold with:
   ```bash
   cd kdp-studio/tools
   python3 -m kdp_studio new --slug <slug> --title "..." --type coloring-book --designs 30
   ```
2. Fill `products/<slug>/brief.md` (concept, audience, cover notes, keyword research).
3. Generate or place interior art in `products/<slug>/pages/page-XX.png`.
4. Build + validate:
   ```bash
   python3 -m kdp_studio pages --slug <slug>      # procedural geometry demo
   python3 -m kdp_studio interior --slug <slug>
   python3 -m kdp_studio cover --slug <slug>
   python3 -m kdp_studio validate --slug <slug>
   ```
5. Write KDP listing draft into `launch/listings/<slug>.md` (title, subtitle, description, 7 keywords, 2 categories).
6. Update root `kdp-studio/README.md` product table.
7. Set `meta.json` → `status: ready` only when interior PDF + cover dimensions exist.

**Quality bar:**
- Every design unique; no near-duplicates across the catalog
- Lines thick enough to color (avoid hairline 1px clutter)
- Safe margins respected
- Cover title readable as an Amazon thumbnail
- If AI art is used, set `ai_assisted: true` and disclose on KDP upload

**Other useful POD ideas (non-coloring):**
- Undated weekly planner (letter)
- Habit tracker / gratitude journal (trade 6×9)
- Garden / reading / hiking logbook (trade)
- Large-print word search (letter)
- Kids activity workbook (letter, simpler art)

**Anti-redundancy:** Read existing `products/*/meta.json` before proposing a SKU. Reject titles that only re-theme an existing pattern set without a clear new audience or job-to-be-done.

---

## Backlog seeds

Coloring
- Bold & Easy Cozy Kitchen Tools (square, thick lines)
- Rainy Day Windows & Houseplants (letter)
- Trail Signs & Woodland Patterns (letter) — nature geometric, not branded parks
- Alphabet Animals for Kids (square)
- Night Sky Constellations (simple, letter)

Useful POD
- Undated Student Weekly Planner
- Home Maintenance Seasonal Log
- Recipe Card Keeper (fill-in pages)
- 90-Day Habit Journal
- Road Trip Mileage & Memory Log
