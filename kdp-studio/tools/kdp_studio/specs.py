"""Shared paths and KDP print constants."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS_PATH = ROOT / "specs" / "trim-sizes.json"
PRODUCTS = ROOT / "products"


def load_specs() -> dict:
    return json.loads(SPECS_PATH.read_text(encoding="utf-8"))


def trim_box(trim_key: str) -> tuple[float, float]:
    specs = load_specs()
    trim = specs["trims"][trim_key]
    return float(trim["width_in"]), float(trim["height_in"])


def gutter_for_pages(page_count: int) -> float:
    specs = load_specs()
    for row in specs["gutter_by_page_count"]:
        if page_count <= row["max_pages"]:
            return float(row["gutter_inches"])
    return float(specs["gutter_by_page_count"][-1]["gutter_inches"])


def spine_width(page_count: int, paper: str = "white") -> float:
    specs = load_specs()
    thickness = float(specs["paper"][paper]["thickness_inches_per_page"])
    return page_count * thickness


def product_dir(slug: str) -> Path:
    return PRODUCTS / slug
