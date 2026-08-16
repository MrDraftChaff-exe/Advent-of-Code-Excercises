"""CLI for KDP Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python -m kdp_studio` from tools/
TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from kdp_studio.build import build_interior_pdf, cover_dimensions
from kdp_studio.cover_art import render_placeholder_cover
from kdp_studio.pages import generate_pages
from kdp_studio.pricing import research_and_price
from kdp_studio.publish import build_publish_package, run_assist
from kdp_studio.specs import PRODUCTS, product_dir
from kdp_studio.validate import validate_product


def cmd_new(args: argparse.Namespace) -> int:
    root = product_dir(args.slug)
    if root.exists() and not args.force:
        print(f"Product already exists: {root} (use --force to overwrite meta)")
        return 1
    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "cover").mkdir(parents=True, exist_ok=True)
    meta = {
        "id": args.slug,
        "title": args.title or args.slug.replace("-", " ").title(),
        "subtitle": args.subtitle or "A printable coloring book for Kindle Direct Publishing",
        "type": args.type,
        "trim": args.trim,
        "bleed": False,
        "single_sided": True,
        "designs": args.designs,
        "page_count_interior": None,
        "paper_color": "white",
        "ink": "black",
        "cover_finish": "matte",
        "list_price_usd": args.price,
        "audience": args.audience or "Adults and teens who enjoy relaxing line art",
        "one_liner": args.one_liner or "Original geometric pages ready to color.",
        "description": (
            "Unwind with clean, original geometric coloring pages. "
            "Printed single-sided so markers and gel pens will not bleed onto the next design."
        ),
        "bullets": [
            f"{args.designs} original black-line designs",
            "Single-sided pages for markers",
            f"{args.trim} trim, KDP paperback ready",
            "Matte cover recommended",
            "No characters or trademarks — original patterns only",
        ],
        "keywords": [
            "coloring book",
            "adult coloring",
            "geometric patterns",
            "relaxing",
            "mandala",
            "stress relief",
            "gift",
        ],
        "categories": [
            "Arts & Photography > Drawing > Coloring Books",
            "Self-Help > Stress Management",
        ],
        "ai_assisted": False,
        "status": "draft",
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    brief = root / "brief.md"
    if not brief.exists() or args.force:
        brief.write_text(
            f"# {meta['title']}\n\n"
            f"**Slug:** `{args.slug}`  \n"
            f"**Type:** {args.type}  \n"
            f"**Trim:** {args.trim}  \n"
            f"**Designs:** {args.designs}\n\n"
            "## Concept\n\n"
            f"{meta['one_liner']}\n\n"
            "## Cover notes\n\n"
            "- Bold title readable at thumbnail size\n"
            "- Show 1–2 sample patterns on the front\n"
            "- Keep spine text short (only if ≥ 79 pages)\n"
            "- Disclose AI art on KDP if used\n",
            encoding="utf-8",
        )
    print(f"Created {root}")
    return 0


def cmd_pages(args: argparse.Namespace) -> int:
    root = product_dir(args.slug)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    count = args.count or int(meta.get("designs", 30))
    trim = args.trim or meta.get("trim", "letter")
    paths = generate_pages(root / "pages", count=count, trim=trim)
    print(f"Wrote {len(paths)} pages → {root / 'pages'}")
    return 0


def cmd_interior(args: argparse.Namespace) -> int:
    root = product_dir(args.slug)
    meta_path = root / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    trim = meta.get("trim", "letter")
    pages = sorted((root / "pages").glob("page-*.png"))
    if not pages:
        print("No pages found. Run: python -m kdp_studio pages --slug", args.slug)
        return 1
    result = build_interior_pdf(
        pages,
        root / "interior.pdf",
        trim=trim,
        single_sided=bool(meta.get("single_sided", True)),
    )
    meta["page_count_interior"] = result["page_count"]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


def cmd_cover(args: argparse.Namespace) -> int:
    if args.slug:
        root = product_dir(args.slug)
        meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
        pages = int(meta.get("page_count_interior") or args.pages or 0)
        trim = meta.get("trim", "letter")
        paper = meta.get("paper_color", "white")
        if not pages:
            print("Set page_count_interior (build interior first) or pass --pages")
            return 1
        dims = cover_dimensions(pages, trim=trim, paper=paper)
        out = root / "cover" / "dimensions.json"
        out.write_text(json.dumps(dims, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(dims, indent=2))
        print(f"Wrote {out}")
        if args.render:
            art = render_placeholder_cover(
                root / "cover" / "wrap-placeholder.png",
                title=meta.get("title", args.slug),
                subtitle=meta.get("subtitle", ""),
                page_count=pages,
                trim=trim,
                paper=paper,
            )
            print(f"Wrote {art['path']} (replace with final art before KDP upload)")
        return 0
    dims = cover_dimensions(args.pages, trim=args.trim, paper=args.paper)
    print(json.dumps(dims, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_product(args.slug)
    if errors:
        print("FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("OK")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    if not PRODUCTS.exists():
        print("No products yet.")
        return 0
    for path in sorted(PRODUCTS.iterdir()):
        if not path.is_dir():
            continue
        meta_path = path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            print(f"{meta.get('id')}\t{meta.get('status')}\t{meta.get('title')}")
        else:
            print(f"{path.name}\t(no meta)")
    return 0


def cmd_price(args: argparse.Namespace) -> int:
    result = research_and_price(
        args.slug,
        query=args.query,
        strategy=args.strategy,
        allow_demo=not args.live_only,
        apply=args.apply,
        comps_file=args.comps_file,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("comps") else 1


def cmd_publish(args: argparse.Namespace) -> int:
    if args.assist or args.live:
        result = run_assist(args.slug, live=bool(args.live))
    else:
        result = build_publish_package(args.slug)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_preview(args: argparse.Namespace) -> int:
    import uvicorn

    print(f"Preview Studio → http://127.0.0.1:{args.port}")
    uvicorn.run(
        "kdp_studio.preview_app:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kdp_studio", description="KDP Studio CLI")
    sub = p.add_subparsers(dest="command", required=True)

    n = sub.add_parser("new", help="Scaffold a product folder")
    n.add_argument("--slug", required=True)
    n.add_argument("--title")
    n.add_argument("--subtitle")
    n.add_argument("--type", default="coloring-book")
    n.add_argument("--trim", default="letter")
    n.add_argument("--designs", type=int, default=30)
    n.add_argument("--price", type=float, default=9.99)
    n.add_argument("--audience")
    n.add_argument("--one-liner")
    n.add_argument("--force", action="store_true")
    n.set_defaults(func=cmd_new)

    pg = sub.add_parser("pages", help="Generate geometric coloring page PNGs")
    pg.add_argument("--slug", required=True)
    pg.add_argument("--count", type=int)
    pg.add_argument("--trim")
    pg.set_defaults(func=cmd_pages)

    interior = sub.add_parser("interior", help="Build interior.pdf from page PNGs")
    interior.add_argument("--slug", required=True)
    interior.set_defaults(func=cmd_interior)

    cover = sub.add_parser("cover", help="Compute KDP cover wrap dimensions")
    cover.add_argument("--slug")
    cover.add_argument("--pages", type=int, default=80)
    cover.add_argument("--trim", default="letter")
    cover.add_argument("--paper", default="white")
    cover.add_argument(
        "--render",
        action="store_true",
        help="Also write a draft wrap-placeholder.png (not for final upload)",
    )
    cover.set_defaults(func=cmd_cover)

    v = sub.add_parser("validate", help="Validate a product against print rules")
    v.add_argument("--slug", required=True)
    v.set_defaults(func=cmd_validate)

    ls = sub.add_parser("list", help="List products")
    ls.set_defaults(func=cmd_list)

    price = sub.add_parser("price", help="Research comparable prices and recommend list price")
    price.add_argument("--slug", required=True)
    price.add_argument("--query", help="Amazon search query override")
    price.add_argument(
        "--strategy",
        choices=["median", "undercut", "premium"],
        default="median",
    )
    price.add_argument("--apply", action="store_true", help="Write recommended price into meta.json")
    price.add_argument(
        "--comps-file",
        help="JSON file of comps: [{title, price_usd, asin?, url?}] (skips Amazon fetch)",
    )
    price.add_argument(
        "--live-only",
        action="store_true",
        help="Do not fall back to demo comps if Amazon fetch fails",
    )
    price.set_defaults(func=cmd_price)

    pub = sub.add_parser("publish", help="Build KDP upload package (no official API)")
    pub.add_argument("--slug", required=True)
    pub.add_argument("--assist", action="store_true", help="Dry-run guided assist message")
    pub.add_argument(
        "--live",
        action="store_true",
        help="Experimental: open KDP Bookshelf in Playwright (manual upload still required)",
    )
    pub.set_defaults(func=cmd_publish)

    prev = sub.add_parser("preview", help="Start local Preview Studio web UI")
    prev.add_argument("--host", default="127.0.0.1")
    prev.add_argument("--port", type=int, default=8765)
    prev.set_defaults(func=cmd_preview)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
