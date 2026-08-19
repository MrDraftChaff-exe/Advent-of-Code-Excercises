# Agent notes

This repo hosts several personal kits. The active coloring-book work lives under [`kdp-studio/`](./kdp-studio/).

## Conflict resolution (mandatory)

There is **no reason to leave a conflicting PR**. Handle conflicts as you go — the same turn you discover them.

### Active tip

Work on the **bold-and-easy square 40-page** stack only. Prefer branching from the current tip of that stack (today: `cursor/fantasy-dresses-cryptids-9aff` / PR #20), not from `main` or from abandoned letter-trim `*-30` branches.

Typical stack (oldest → tip):

1. `cursor/bold-easy-six-themes-9aff` (#11)
2. `cursor/buildings-upload-env-9aff` (#13)
3. `cursor/thematic-covers-barcode-9aff` (#17)
4. `cursor/fantasy-dresses-cryptids-9aff` (#20)

### Rules while coding

1. **Merge the PR base into your head before you finish** (and again if the base moves). Do not open or leave a `CONFLICTING` / `DIRTY` PR.
2. **One active tip.** Do not start a parallel PR that edits the same `kdp-studio/products/<slug>/` files another open PR already owns.
3. **Do not resurrect** letter-trim theme books (`chemistry-30`, `forest-animals-30`, `math-30`, `physical-science-30`, `sea-life-30`, `space-30`, `sports-30`). See [`kdp-studio/PRODUCT_FACTORY.md`](./kdp-studio/PRODUCT_FACTORY.md). Those PRs (#7, #14) are legacy.
4. **Resolve immediately** when git reports conflicts — same session, then push.

### How to resolve common conflicts

| Conflict | Keep |
| --- | --- |
| Product interiors / pages / PDFs | Newest intentional art (cleaned bold-and-easy pages beat older rough gens) |
| Cover wraps / `cover_art.py` | Thematic retail backs + empty KDP barcode well; **no** printed “AI-assisted — disclose on KDP” footer |
| `cloud-agent-start.sh` | Non-blocking start: `nohup` Preview Studio, then **exit 0**. Never `exec` a forever sleep — that hangs Cloud Agent Save |
| `.cursor/environment.json` | Guarded `if [ -f … ]` install/start so missing scripts do not crash setup |
| Pricing / demo list price | Prefer the branch that intentionally changed price for that SKU |

### When two agents collide

- Rebase or merge the other agent’s tip into yours as soon as you see divergence.
- Prefer their completed product art if you were only scaffolding; prefer yours if you were the cleanup pass (document which side you kept in the PR body).
- Never “defer conflicts for later.”
