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


DEFAULT_PREFIXES = ("tv", "tstats", "tci")


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


def parse_prefixes(raw: str) -> tuple[str, ...]:
    """Parse a comma/space-separated prefix list. Empty means no prefixes."""
    raw = raw.strip()
    if not raw:
        return ()
    parts = [part.strip() for part in raw.replace(" ", ",").split(",") if part.strip()]
    if not parts:
        return ()
    return tuple(parts)


def complete_group_count(count: int, group_size: int) -> int:
    """Round *count* up so every paste group has *group_size* items."""
    if group_size <= 1:
        return count
    remainder = count % group_size
    if remainder:
        return count + (group_size - remainder)
    return count


def apply_rotating_prefixes(
    codes: list[str], prefixes: tuple[str, ...] = DEFAULT_PREFIXES
) -> list[str]:
    """Prepend prefixes in repeating order with a space: tv 3ppsc0, ..."""
    if not prefixes:
        return list(codes)
    return [
        f"{prefixes[index % len(prefixes)]} {code}"
        for index, code in enumerate(codes)
    ]


def grouped(items: list[str], group_size: int) -> list[list[str]]:
    """Split items into consecutive groups of *group_size*."""
    if group_size < 1:
        raise ValueError("group size must be at least 1")
    return [items[index : index + group_size] for index in range(0, len(items), group_size)]


def format_paste_groups(groups: list[list[str]]) -> str:
    """Join groups with a blank line so each tv/tstats/tci set is easy to copy."""
    return "\n\n".join("\n".join(group) for group in groups if group)


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
        "--prefixes",
        default="",
        help="comma-separated prefixes to prepend in rotating order, e.g. tv,tstats,tci",
    )
    parser.add_argument(
        "--group-size",
        type=int,
        default=None,
        help="lines per paste group (default: number of prefixes, or 1)",
    )
    return parser


def resolve_group_size(
    prefixes: tuple[str, ...], group_size: int | None, count: int
) -> int:
    if group_size is None:
        return len(prefixes) if prefixes else max(count, 1)
    if group_size < 1:
        raise ValueError("group size must be at least 1")
    return group_size


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        alphabet = parse_alphabet(args.alphabet)
        prefixes = parse_prefixes(args.prefixes)
        group_size = resolve_group_size(prefixes, args.group_size, args.count)
        count = complete_group_count(args.count, group_size)
        tagged = apply_rotating_prefixes(next_codes(args.code, count, alphabet), prefixes)
        print(format_paste_groups(grouped(tagged, group_size)))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
