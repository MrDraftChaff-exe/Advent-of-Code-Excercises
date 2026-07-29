#!/usr/bin/env python3
"""Normalize a wget WordPress mirror for local static hosting."""
from __future__ import annotations

import re
import shutil
import sys
import urllib.request
from pathlib import Path

PAGE_MAP = {
    "11": "about-us/",
    "15": "our-queens-and-toms/",
    "17": "available-kittens/",
    "19": "past-kittens/",
    "26": "contact/",
}

TEXT_EXTS = {".html", ".css", ".js", ".svg", ".xml", ".json", ".txt"}


def depth_prefix(rel_path: Path) -> str:
    depth = len(rel_path.parts) - 1
    return "" if depth <= 0 else "../" * depth


def rename_query_files(root: Path) -> dict[str, str]:
    renames: dict[str, str] = {}
    files = sorted(
        [p for p in root.rglob("*") if p.is_file() and "?" in p.name],
        key=lambda p: len(str(p)),
        reverse=True,
    )
    for old in files:
        name = old.name
        if name.startswith("index.html?p=") or name.startswith("embed?url="):
            continue
        base = name.split("?", 1)[0]
        new = old.with_name(base)
        rel_old = str(old.relative_to(root)).replace("\\", "/")
        if new.exists() and new != old:
            old.unlink()
            renames[rel_old] = str(new.relative_to(root)).replace("\\", "/")
            continue
        old.rename(new)
        renames[rel_old] = str(new.relative_to(root)).replace("\\", "/")
    return renames


def rewrite_text_files(root: Path, renames: dict[str, str]) -> None:
    replacements = []
    for old, new in renames.items():
        replacements.append((old, new))
        replacements.append((old.replace("?", "%3F"), new))
    replacements.sort(key=lambda x: len(x[0]), reverse=True)

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        orig = text
        rel = path.relative_to(root)
        prefix = depth_prefix(rel)

        for old, new in replacements:
            text = text.replace(old, new)

        for pid, dest in PAGE_MAP.items():
            for pat in (
                f"index.html?p={pid}.html",
                f"index.html%3Fp={pid}.html",
                f"index.html%3Fp%3D{pid}.html",
                f"../index.html?p={pid}.html",
                f"../index.html%3Fp={pid}.html",
                f"./index.html?p={pid}.html",
                f"./index.html%3Fp={pid}.html",
            ):
                text = text.replace(pat, f"{prefix}{dest}")

        text = re.sub(
            r"(?:\./|\.\./)*index\.html(?:\?|%3F)p(?:=|%3D)(\d+)\.html",
            lambda m: f"{prefix}{PAGE_MAP.get(m.group(1), 'index.html')}",
            text,
        )

        # Absolute live URLs -> local relative (pages + assets)
        for host in (
            "https://featherhillmainecoons.com/",
            "https://www.featherhillmainecoons.com/",
            "http://featherhillmainecoons.com/",
            "//featherhillmainecoons.com/",
        ):
            text = text.replace(host, prefix)

        # Undo wget mangling if absolute URL was replaced into index.html + path
        text = text.replace(f"{prefix}index.htmlwp-content/", f"{prefix}wp-content/")
        text = text.replace("index.htmlwp-content/", "wp-content/")
        text = text.replace("index.htmlwp-includes/", "wp-includes/")
        text = text.replace("../index.htmlwp-content/", "../wp-content/")

        def clean_asset(m: re.Match[str]) -> str:
            left, url, right = m.group(1), m.group(2), m.group(3)
            if url.startswith(("http://", "https://", "//", "data:", "mailto:", "#", "tel:", "about:")):
                return m.group(0)
            url2 = re.split(r"%3F|\?", url, maxsplit=1)[0]
            return f"{left}{url2}{right}"

        text = re.sub(r"(url\([\'\"]?)([^\)\'\"]+)([\'\"]?\))", clean_asset, text)
        text = re.sub(r"((?:href|src)=[\'\"])([^\'\"]+)([\'\"])", clean_asset, text)
        text = re.sub(r"<link[^>]+wp-json/oembed[^>]*>\s*", "", text)
        text = re.sub(r"<link[^>]+xmlrpc\.php[^>]*>\s*", "", text)
        text = re.sub(r'<link[^>]+type="application/json"[^>]*>\s*', "", text)

        if text != orig:
            path.write_text(text, encoding="utf-8")


def cleanup_junk(root: Path) -> None:
    for junk in root.glob("index.html?p=*.html"):
        junk.unlink()
    for junk_dir in ("feed", "comments", "wp-json"):
        p = root / junk_dir
        if p.exists():
            shutil.rmtree(p)


def fetch_missing_assets(root: Path, base_url: str = "https://featherhillmainecoons.com/") -> None:
    missing: set[str] = set()
    for html in root.rglob("*.html"):
        text = html.read_text(encoding="utf-8", errors="ignore")
        for attr in re.findall(r'(?:src|data-src|data-lazy-src)=["\']([^"\']+)["\']', text):
            if attr.startswith(("http://", "https://", "//", "data:", "#", "mailto:", "about:", "tel:")):
                continue
            clean = attr.split("?")[0].split("#")[0]
            if not clean or clean.endswith("/"):
                continue
            target = (html.parent / clean).resolve()
            try:
                rel = str(target.relative_to(root.resolve())).replace("\\", "/")
            except ValueError:
                continue
            if not target.exists() and any(
                rel.lower().endswith(ext)
                for ext in (".webp", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".woff", ".woff2", ".css", ".js")
            ):
                missing.add(rel)

    for rel in sorted(missing):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = base_url + rel
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                dest.write_bytes(response.read())
            print(f"fetched {rel}")
        except Exception as exc:  # noqa: BLE001
            print(f"skip {rel}: {exc}")


def normalize(root: Path) -> None:
    renames = rename_query_files(root)
    rewrite_text_files(root, renames)
    cleanup_junk(root)
    fetch_missing_assets(root)
    print(f"Normalized {root} ({len(renames)} renames)")


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    normalize(target)
