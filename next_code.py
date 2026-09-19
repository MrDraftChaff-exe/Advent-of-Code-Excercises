#!/usr/bin/env python3
"""Increment short codes in a custom alphabet (base-N odometer).

The default alphabet is the 30-character no-vowel, no-L set:

    g r d x v c y 0 f j 7 5 p 4 q 3 s 6 2 8 z t m b h 9 n 1 k w

Codes are treated as positional numerals with that digit order. The
rightmost character is least significant. Incrementing ``3ppscy``
therefore advances ``y`` (index 6) to ``0`` (index 7) with no carry:

    3ppscy -> 3ppsc0
"""

from __future__ import annotations

import argparse
import sys

DEFAULT_ALPHABET = "grdxvcy0fj75p4q3s628ztmbh9n1kw"


def parse_alphabet(raw: str) -> str:
    """Accept a compact string or a hyphen/space/comma-separated list."""
    if "-" in raw and raw.replace("-", "").isalnum():
        parts = [p for p in raw.split("-") if p]
        if parts and all(len(p) == 1 for p in parts):
            raw = "".join(parts)
    else:
        for sep in (" ", ",", "|"):
            if sep in raw:
                parts = [p for p in raw.split(sep) if p]
                if parts and all(len(p) == 1 for p in parts):
                    raw = "".join(parts)
                break
    if len(raw) < 2:
        raise ValueError("alphabet must contain at least 2 characters")
    if len(set(raw)) != len(raw):
        raise ValueError("alphabet characters must be unique")
    return raw


def code_to_int(code: str, alphabet: str = DEFAULT_ALPHABET) -> int:
    """Decode a code as an integer in the custom base."""
    index = {ch: i for i, ch in enumerate(alphabet)}
    value = 0
    base = len(alphabet)
    for ch in code:
        if ch not in index:
            raise ValueError(f"character {ch!r} is not in the alphabet")
        value = value * base + index[ch]
    return value


def int_to_code(value: int, alphabet: str = DEFAULT_ALPHABET, width: int = 1) -> str:
    """Encode a non-negative integer, padding to at least ``width`` digits."""
    if value < 0:
        raise ValueError("value must be non-negative")
    base = len(alphabet)
    if value == 0:
        return alphabet[0] * max(width, 1)
    digits: list[str] = []
    n = value
    while n:
        n, rem = divmod(n, base)
        digits.append(alphabet[rem])
    while len(digits) < width:
        digits.append(alphabet[0])
    return "".join(reversed(digits))


DEFAULT_SUFFIXES = ("tv", "tstats", "tci")


def next_code(code: str, alphabet: str = DEFAULT_ALPHABET) -> str:
    """Return the next code in sequence (rightmost digit increments first)."""
    if not code:
        raise ValueError("code must be non-empty")
    alphabet = parse_alphabet(alphabet)
    return int_to_code(code_to_int(code, alphabet) + 1, alphabet, width=len(code))


def next_codes(
    code: str, count: int, alphabet: str = DEFAULT_ALPHABET
) -> list[str]:
    """Return the next *count* codes after *code*."""
    if count < 1:
        raise ValueError("count must be at least 1")
    alphabet = parse_alphabet(alphabet)
    current = code
    results: list[str] = []
    for _ in range(count):
        current = next_code(current, alphabet)
        results.append(current)
    return results


def parse_suffixes(raw: str) -> tuple[str, ...]:
    """Parse a comma/space-separated suffix list. Empty means no suffixes."""
    raw = raw.strip()
    if not raw:
        return ()
    parts = [part.strip() for part in raw.replace(" ", ",").split(",") if part.strip()]
    if not parts:
        return ()
    return tuple(parts)


def apply_rotating_suffixes(
    codes: list[str], suffixes: tuple[str, ...] = DEFAULT_SUFFIXES
) -> list[str]:
    """Append suffixes in repeating order: tv, tstats, tci, tv, ..."""
    if not suffixes:
        return list(codes)
    return [f"{code}{suffixes[index % len(suffixes)]}" for index, code in enumerate(codes)]


def split_groups(items: list[str], group_count: int = 3) -> list[list[str]]:
    """Split items into *group_count* contiguous paste groups."""
    if group_count < 1:
        raise ValueError("group count must be at least 1")
    if not items:
        return [[] for _ in range(group_count)]
    size, extra = divmod(len(items), group_count)
    groups: list[list[str]] = []
    start = 0
    for index in range(group_count):
        length = size + (1 if index < extra else 0)
        groups.append(items[start : start + length])
        start += length
    return groups


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find the next short code in a custom-alphabet sequence."
    )
    parser.add_argument("code", help="starting code, e.g. 3ppscy")
    parser.add_argument(
        "-a",
        "--alphabet",
        default=DEFAULT_ALPHABET,
        help="custom alphabet string or hyphen-separated sequence",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="how many successive codes to print (default: 1)",
    )
    parser.add_argument(
        "--suffixes",
        default="",
        help="comma-separated suffixes to append in rotating order, e.g. tv,tstats,tci",
    )
    parser.add_argument(
        "--groups",
        type=int,
        default=1,
        help="split output into this many contiguous paste groups (default: 1)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        alphabet = parse_alphabet(args.alphabet)
        suffixes = parse_suffixes(args.suffixes)
        codes = apply_rotating_suffixes(next_codes(args.code, args.count, alphabet), suffixes)
        groups = split_groups(codes, args.groups)
        blocks = ["\n".join(group) for group in groups if group]
        print("\n\n".join(blocks))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
