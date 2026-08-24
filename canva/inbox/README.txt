Drop source images here (jpg/png/webp), then run:

  python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox

For 392 images that also have titles/hooks in the Facts-or-Whacks CSV:

  python3 scripts/prepare_canva_bulk.py --images-dir canva/inbox --csv facts-or-whacks-30-videos.csv

Files with "-raw" in the stem are skipped. Output is gitignored under output/canva/.

Canva Apps → Bulk Create is capped at 300 rows, so 392 images become:
  output/canva/bulk-create-batch-01-of-02.xlsx  (300)
  output/canva/bulk-create-batch-02-of-02.xlsx  (92)

Or import into a Canva Sheet and use Actions → Bulk Create designs (no 300 cap).

This folder is for local drops only — do not commit the 392 originals.
