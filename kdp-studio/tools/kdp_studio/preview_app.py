"""Local Preview Studio for KDP products."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from kdp_studio.pricing import research_and_price
from kdp_studio.publish import build_publish_package, stage_upload_kit
from kdp_studio.specs import PRODUCTS, ROOT, product_dir
from kdp_studio.validate import validate_product

PREVIEW_DIR = ROOT / "preview"
STATIC_DIR = PREVIEW_DIR / "static"

app = FastAPI(title="KDP Studio Preview")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _load_meta(slug: str) -> dict:
    path = product_dir(slug) / "meta.json"
    if not path.exists():
        raise HTTPException(404, f"Unknown product: {slug}")
    return json.loads(path.read_text(encoding="utf-8"))


def _list_products() -> list[dict]:
    items = []
    if not PRODUCTS.exists():
        return items
    for path in sorted(PRODUCTS.iterdir()):
        meta_path = path / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pages = sorted((path / "pages").glob("page-*.png")) if (path / "pages").exists() else []
        items.append(
            {
                "id": meta.get("id", path.name),
                "title": meta.get("title", path.name),
                "subtitle": meta.get("subtitle", ""),
                "type": meta.get("type"),
                "status": meta.get("status"),
                "list_price_usd": meta.get("list_price_usd"),
                "designs": meta.get("designs"),
                "page_count_interior": meta.get("page_count_interior"),
                "page_png_count": len(pages),
                "has_interior": (path / "interior.pdf").exists(),
                "has_cover": (path / "cover" / "wrap-placeholder.png").exists()
                or (path / "cover" / "dimensions.json").exists(),
                "has_pricing": (path / "pricing.json").exists(),
            }
        )
    return items


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    index = PREVIEW_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.get("/api/products")
def api_products() -> dict:
    return {"products": _list_products()}


@app.get("/api/products/{slug}")
def api_product(slug: str) -> dict:
    root = product_dir(slug)
    meta = _load_meta(slug)
    pages = sorted((root / "pages").glob("page-*.png")) if (root / "pages").exists() else []
    pricing = None
    if (root / "pricing.json").exists():
        pricing = json.loads((root / "pricing.json").read_text(encoding="utf-8"))
    dims = None
    if (root / "cover" / "dimensions.json").exists():
        dims = json.loads((root / "cover" / "dimensions.json").read_text(encoding="utf-8"))
    listing = None
    listing_path = ROOT / "launch" / "listings" / f"{slug}.md"
    if listing_path.exists():
        listing = listing_path.read_text(encoding="utf-8")
    brief = None
    if (root / "brief.md").exists():
        brief = (root / "brief.md").read_text(encoding="utf-8")
    publish_fields = None
    if (root / "publish" / "kdp-fields.json").exists():
        publish_fields = json.loads((root / "publish" / "kdp-fields.json").read_text(encoding="utf-8"))
    kit = root / "upload-kit"
    kit_files = sorted(p.name for p in kit.iterdir()) if kit.exists() else []
    paste_fields = {}
    paste_dir = kit / "paste-fields"
    if paste_dir.exists():
        for txt in sorted(paste_dir.glob("*.txt")):
            paste_fields[txt.stem] = txt.read_text(encoding="utf-8")
    return {
        "meta": meta,
        "pages": [p.name for p in pages],
        "pricing": pricing,
        "cover_dimensions": dims,
        "listing_md": listing,
        "brief_md": brief,
        "publish_fields": publish_fields,
        "validation": validate_product(slug),
        "assets": {
            "interior_pdf": (root / "interior.pdf").exists(),
            "cover_png": (root / "cover" / "wrap-placeholder.png").exists(),
            "upload_kit": kit.exists(),
        },
        "upload_kit": {
            "ready": kit.exists(),
            "files": kit_files,
            "paste_fields": paste_fields,
            "guide_url": f"/api/products/{slug}/upload-kit/00-UPLOAD-NOW.md" if kit.exists() else None,
        },
    }


@app.get("/api/products/{slug}/pages/{name}")
def api_page_file(slug: str, name: str):
    if "/" in name or ".." in name:
        raise HTTPException(400, "Invalid page name")
    # Prefer SVG (true vectors — stay smooth at any zoom); fall back to PNG
    root = product_dir(slug) / "pages"
    if name.endswith(".svg"):
        path = root / name
        if path.exists():
            return FileResponse(path, media_type="image/svg+xml")
        raise HTTPException(404)
    if name.endswith(".png"):
        svg = root / name.replace(".png", ".svg")
        if svg.exists():
            return FileResponse(svg, media_type="image/svg+xml")
        path = root / name
        if path.exists():
            return FileResponse(path, media_type="image/png")
        raise HTTPException(404)
    raise HTTPException(400, "Invalid page name")


@app.get("/api/products/{slug}/cover.png")
def api_cover(slug: str):
    path = product_dir(slug) / "cover" / "wrap-placeholder.png"
    if not path.exists():
        raise HTTPException(404, "No cover preview yet")
    return FileResponse(path, media_type="image/png")


@app.get("/api/products/{slug}/interior.pdf")
def api_interior(slug: str):
    path = product_dir(slug) / "interior.pdf"
    if not path.exists():
        raise HTTPException(404, "No interior.pdf yet")
    return FileResponse(path, media_type="application/pdf")


@app.post("/api/products/{slug}/research-price")
def api_research_price(
    slug: str,
    apply: bool = Query(False),
    strategy: str = Query("median"),
    query: str | None = None,
):
    _load_meta(slug)
    return research_and_price(slug, query=query, strategy=strategy, apply=apply, allow_demo=True)


@app.post("/api/products/{slug}/publish-package")
def api_publish_package(slug: str):
    result = build_publish_package(slug)
    if not result.get("ok"):
        raise HTTPException(400, {"errors": result.get("errors")})
    return result


@app.post("/api/products/{slug}/upload-kit")
def api_stage_upload_kit(slug: str):
    result = stage_upload_kit(slug)
    if not result.get("ok"):
        raise HTTPException(400, {"errors": result.get("errors")})
    return result


@app.get("/api/products/{slug}/upload-kit/{name:path}")
def api_upload_kit_file(slug: str, name: str):
    if ".." in name or name.startswith("/"):
        raise HTTPException(400, "Invalid file name")
    path = product_dir(slug) / "upload-kit" / name
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Upload-kit file not found — stage the kit first")
    media = "application/octet-stream"
    if name.endswith(".pdf"):
        media = "application/pdf"
    elif name.endswith(".png"):
        media = "image/png"
    elif name.endswith(".json"):
        media = "application/json"
    elif name.endswith(".md") or name.endswith(".txt"):
        media = "text/plain; charset=utf-8"
    return FileResponse(path, media_type=media, filename=path.name)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "kdp_studio.preview_app:app",
        host="0.0.0.0",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
