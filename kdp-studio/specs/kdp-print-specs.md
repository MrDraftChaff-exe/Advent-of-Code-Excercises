# KDP Print Specs (Coloring Books & Useful POD)

Reference checklist for Amazon Kindle Direct Publishing paperback interiors and covers. Confirm against [KDP Help → Trim Size, Bleed, and Margins](https://kdp.amazon.com/help/topic/GVBQ3CMEQW3W2VL6) before every upload — Amazon can change rules.

## Coloring books (default)

| Setting | Recommendation |
| --- | --- |
| Trim | **8.5" × 11"** (letter) for adult; **8.5" × 8.5"** for kids / bold-easy |
| Bleed | **No bleed** if art sits in a white margin (simpler). Use bleed only if art goes to the edge |
| DPI | **300 DPI** at final print size (never upscale 72 DPI art) |
| Color | Interior: **black ink / grayscale**. Cover: **CMYK-ready PDF** |
| Layout | **Single-sided**: illustration → blank → illustration → blank |
| Page count | ~40 designs → ~80 interior pages; sweet spot often 80–120 pages |
| Outside margin | ≥ 0.25" no-bleed; ≥ 0.375" with bleed (use 0.5" for safety) |
| Gutter | ≥ 0.375" for books ≤ 150 pages |
| Paper | White for coloring; cream for journals |
| Cover finish | Matte (hides fingerprints; common for coloring) |

## Cover wrap formula

```
cover_width  = bleed + back + spine + front + bleed
cover_height = bleed + trim_height + bleed
spine_width  = page_count × paper_thickness
```

White paper ≈ **0.002252"** per page. Spine text only when page count ≥ **79**.

Use `python3 -m kdp_studio cover --pages N --trim letter` for exact inches/pixels.

## Other useful POD SKUs

| Type | Trim | Notes |
| --- | --- | --- |
| Daily / weekly planner | 8.5×11 or 6×9 | Dated or undated; thick enough for writing |
| Habit / gratitude journal | 6×9 or 5.5×8.5 | Lined or prompt pages |
| Puzzle book | 8.5×11 | Word search, sudoku — leave answer key |
| Activity / kids workbook | 8.5×11 | Larger type, simpler art |
| Logbooks (garden, reading, hiking) | 6×9 | Repeatable form pages |

## Rejection hot spots

1. Interior PDF trim size ≠ KDP trim selection  
2. Soft / jagged lines (< 300 DPI)  
3. Critical art or text in the gutter / outside safe zone  
4. Missing blank backs on coloring books (marker bleed-through complaints)  
5. Low-contrast covers or unreadable spine  
6. Trademarked characters / logos without rights  

## AI disclosure

If any interior or cover art is AI-generated, disclose that on KDP upload per Amazon’s current AI content policy.
