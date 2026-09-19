#!/usr/bin/env python3
"""Tests for custom-alphabet code incrementing."""

import unittest

from next_code import DEFAULT_ALPHABET, next_code, parse_alphabet


class ParseAlphabetTests(unittest.TestCase):
    def test_hyphen_separated_alphabet(self) -> None:
        raw = "g-r-d-x-v-c-y-0-f-j-7-5-p-4-q-3-s-6-2-8-z-t-m-b-h-9-n-1-k-w"
        self.assertEqual(parse_alphabet(raw), DEFAULT_ALPHABET)

    def test_compact_alphabet_is_unchanged(self) -> None:
        self.assertEqual(parse_alphabet(DEFAULT_ALPHABET), DEFAULT_ALPHABET)


class NextCodeTests(unittest.TestCase):
    def test_starting_code_3ppscy(self) -> None:
        self.assertEqual(next_code("3ppscy"), "3ppsc0")

    def test_simple_increment_without_carry(self) -> None:
        self.assertEqual(next_code("g"), "r")
        self.assertEqual(next_code("r"), "d")

    def test_carry_wraps_to_next_place(self) -> None:
        self.assertEqual(next_code("w"), "rg")
        self.assertEqual(next_code("gw"), "rg")
        self.assertEqual(next_code("ww"), "rgg")

    def test_hyphenated_alphabet_matches_default(self) -> None:
        alphabet = parse_alphabet(
            "g-r-d-x-v-c-y-0-f-j-7-5-p-4-q-3-s-6-2-8-z-t-m-b-h-9-n-1-k-w"
        )
        self.assertEqual(next_code("3ppscy", alphabet), "3ppsc0")

    def test_rejects_empty_code(self) -> None:
        with self.assertRaises(ValueError):
            next_code("")

    def test_rejects_unknown_symbol(self) -> None:
        with self.assertRaises(ValueError):
            next_code("3ppsca")


if __name__ == "__main__":
    unittest.main()
