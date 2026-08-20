# KDP Studio — migration handoff

Pen name **Elsie Wren**. Interior style is locked in [`STYLE.md`](./STYLE.md): square 8.5×8.5, 40 designs, single-sided, thick closed outlines, no interior text, no grayscale, no hatching, no solid black fills.

This file is the resume point for a new machine or Cloud Agent. The git branch is the full package (interiors, art-source, wraps, listings). Rebuild the upload-only archive after checkout:

```bash
python3 kdp-studio/scripts/package_migration.py
```

That refreshes:

| Path | In git? |
| --- | --- |
| `kdp-studio/migration/manifest.json` | yes |
| `kdp-studio/migration/INDEX.md` | yes |
| `kdp-studio/migration/CHECKSUMS.sha256` | yes |
| `kdp-studio-migration.tar.gz` | **no** — written to `/tmp` (or `/workspace` if `/tmp` fails) |

`/opt/cursor/artifacts` is often a zero-capacity store mount on Cloud Agents. Do not rely on it for the tarball. The archive contains publish kits, cover heroes, listings, `STYLE.md`, and this file. Page PNGs and `art-source` stay in git under `products/<slug>/`.

Verify interiors after copy:

```bash
cd kdp-studio && sha256sum -c migration/CHECKSUMS.sha256
```

## Source of truth

| What | Where |
| --- | --- |
| Catalog + four trend interiors | `cursor/trend-coloring-books-9aff` ([PR #22](https://github.com/MrDraftChaff-exe/Advent-of-Code-Excercises/pull/22)) |
| This packaging branch | `cursor/kdp-migration-package-9aff` |
| Fantasy / Yokai / etc. already merged | `cursor/thematic-covers-barcode-9aff` via [PR #20](https://github.com/MrDraftChaff-exe/Advent-of-Code-Excercises/pull/20) |
| Environment | `.cursor/environment.json` (repo-managed). Preview Studio on port **8765**. |

Checkout this packaging branch (or the trend branch) before generating art. Older Cloud Agent boots often land on `cursor/kdp-coloring-books-9aff` (letter 30-page books). Fetch and reset:

```bash
git fetch origin cursor/kdp-migration-package-9aff
git checkout -B cursor/kdp-migration-package-9aff origin/cursor/kdp-migration-package-9aff
```

## Upload-ready SKUs (40 pages, interior PDF + wrap)

Quiet Places, Stained Glass, Cars, Planes, Buildings, Food, Mountains, Fantasy, Princess Dresses, Cryptids, Yokai, World Cryptids, Construction, Mushrooms, Botanicals, Corgis, Cottagecore.

Each kit is `products/<slug>/publish/`: `interior.pdf`, `cover/wrap-placeholder.png`, `kdp-fields.json`, `UPLOAD.md`. Live prices and SHA256 hashes are in [`migration/INDEX.md`](./migration/INDEX.md). Do **not** buy a barcode. Leave the white 2.0" × 1.2" well empty (0.25" from spine and bottom). Disclose AI on the KDP form, never as printed wrap text.

## Registered titles without interiors yet

Scenes, cover palettes, and colored cover heroes exist. Generate line art → `to_ink()` into exact `art-source/<prefix>-NN.png` slots (do **not** run `inkify_bold_easy.py` CLI on a glob; it re-numbers). Then:

```bash
python3 scripts/build_theme_book.py <slug>
```

| Slug | Title |
| --- | --- |
| `celestial-40` | Celestial Mandalas |
| `cozy-critters-40` | Cozy Critters |
| `dragons-40` | Dragons |
| `spooky-cute-40` | Spooky Cute |
| `holidays-40` | Holidays |
| `chapel-gardens-40` | Chapel Gardens |
| `slow-mornings-40` | Slow Mornings |
| `moon-magic-40` | Moon Magic |
| `dark-academia-40` | Dark Academia |
| `zen-gardens-40` | Zen Gardens |
| `retro-40` | Retro Days |
| `rest-easy-40` | Rest Easy |
| `dinosaurs-40` | Dinosaurs |
| `star-signs-40` | Star Signs |

Skipped as books (`STYLE.md`): grayscale photo coloring, profanity lettering, labeled anatomy.

## Open quality issue (not fixed on this pack)

Reviewer report: **sizing issues and random missing lines across coloring books**. A full QA pass was interrupted by VM timeouts. Next agent should inspect `products/*/pages/page-01.png` plus a mid and last page per SKU, then `art_import._normalize_quiet_raster` / `inkify_bold_easy.to_ink` if lines are torn after placement. Do not re-binarize after LANCZOS resize.

## Environment

Install/start scripts: `kdp-studio/scripts/cloud-agent-install.sh` and `cloud-agent-start.sh`. `start` launches Preview Studio with **nohup and exits** so Cloud Agent Save does not hang.

This Cloud Agent run is repository-managed (`.cursor/environment.json`) with **no saved environment public ID**, so a Cursor Environment Builds migrate cannot be triggered from here. Clone the branch; do not wait on a snapshot.

Preview:

```bash
cd kdp-studio/tools
python3 -m kdp_studio preview --host 0.0.0.0 --port 8765
```
