#!/usr/bin/env python3
"""Increment a code using a custom positional alphabet."""

from __future__ import annotations

import argparse
import sys

DEFAULT_ALPHABET = "grdxvcy0fj75p4q3s628ztmbh9n1kw"


def parse_alphabet(raw: str) -> str:
    """Accept a compact alphabet or a hyphen-separated listing of symbols."""
    alphabet = raw.replace("-", "") if "-" in raw else raw
    if len(alphabet) < 2:
        raise ValueError("alphabet must contain at least two symbols")
    if len(set(alphabet)) != len(alphabet):
        raise ValueError("alphabet symbols must be unique")
    return alphabet


def next_code(code: str, alphabet: str = DEFAULT_ALPHABET) -> str:
    """Return the next code after *code* in the given alphabet.

    Codes are treated as big-endian numbers in base ``len(alphabet)``.
    The rightmost symbol increments first; overflow wraps to the first
    alphabet symbol and carries left. A full overflow grows the code by
    one symbol (``w`` -> ``rg`` when ``g`` is zero and ``r`` is one).
    """
    if not code:
        raise ValueError("code must not be empty")

    index = {symbol: position for position, symbol in enumerate(alphabet)}
    unknown = sorted({symbol for symbol in code if symbol not in index})
    if unknown:
        pretty = ", ".join(repr(symbol) for symbol in unknown)
        raise ValueError(f"code contains symbols not in the alphabet: {pretty}")

    symbols = list(code)
    for position in range(len(symbols) - 1, -1, -1):
        next_index = index[symbols[position]] + 1
        if next_index < len(alphabet):
            symbols[position] = alphabet[next_index]
            return "".join(symbols)
        symbols[position] = alphabet[0]

    return alphabet[1] + "".join(symbols)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find the next code in a custom-alphabet sequence."
    )
    parser.add_argument("code", help="Current code, for example 3ppscy")
    parser.add_argument(
        "-a",
        "--alphabet",
        default=DEFAULT_ALPHABET,
        help="Alphabet as a compact string or hyphen-separated symbols",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        alphabet = parse_alphabet(args.alphabet)
        print(next_code(args.code, alphabet))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
