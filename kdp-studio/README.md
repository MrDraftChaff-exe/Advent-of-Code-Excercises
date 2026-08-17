# KDP Studio

Toolkit for creating **Quiet Places–style** bold & easy coloring books and other useful **Amazon KDP** paperbacks.

**Art foundation:** Read [`STYLE.md`](./STYLE.md) first. Interior coloring art must always follow that Quiet Places bold-and-easy style — never procedural clip-art, never page lettering, never overly dark fills.

## Preview

```bash
cd kdp-studio
./scripts/preview.sh
# → http://127.0.0.1:8765
```

## Active product

| SKU | Type | Trim | Price | Folder |
| --- | --- | --- | --- | --- |
| Quiet Places — 40 Bold & Easy Designs | coloring-book | square 8.5×8.5 | $10.99 | `products/quiet-places-40` |

Build / rebuild:

```bash
python3 scripts/inkify_quiet_places.py /path/to/qp-gen-dir
python3 scripts/build_theme_book.py quiet-places-40
```

Publish package: `products/quiet-places-40/publish/`

Pen name: **Elsie Wren**. Disclose AI-assisted art on KDP when applicable.

## Structure

```text
kdp-studio/
  STYLE.md             # Mandatory art style (Quiet Places foundation)
  products/            # quiet-places-40 only
  scripts/             # inkify + build_theme_book
  tools/kdp_studio/    # CLI / import / cover / validate
  launch/              # Upload checklist + listing
  PRODUCT_FACTORY.md   # How to add the next SKU (same style only)
```

See [`specs/kdp-print-specs.md`](./specs/kdp-print-specs.md) and [`launch/CHECKLIST.md`](./launch/CHECKLIST.md).
