#!/usr/bin/env python3
"""Tests for custom-alphabet short-code incrementing."""

import unittest

from next_code import (
    DEFAULT_ALPHABET,
    code_to_int,
    int_to_code,
    next_code,
    parse_alphabet,
)


HYPHENATED = "g-r-d-x-v-c-y-0-f-j-7-5-p-4-q-3-s-6-2-8-z-t-m-b-h-9-n-1-k-w"


class ParseAlphabetTests(unittest.TestCase):
    def test_default_has_30_unique_chars(self) -> None:
        self.assertEqual(len(DEFAULT_ALPHABET), 30)
        self.assertEqual(len(set(DEFAULT_ALPHABET)), 30)

    def test_hyphenated_form_matches_default(self) -> None:
        self.assertEqual(parse_alphabet(HYPHENATED), DEFAULT_ALPHABET)

    def test_rejects_duplicates(self) -> None:
        with self.assertRaises(ValueError):
            parse_alphabet("aba")


class NextCodeTests(unittest.TestCase):
    def test_puzzle_starting_code(self) -> None:
        self.assertEqual(next_code("3ppscy"), "3ppsc0")

    def test_hyphenated_alphabet_argument(self) -> None:
        self.assertEqual(next_code("3ppscy", HYPHENATED), "3ppsc0")

    def test_simple_increment_uses_next_alphabet_char(self) -> None:
        self.assertEqual(next_code("g"), "r")
        self.assertEqual(next_code("3ppsc0"), "3ppscf")

    def test_carry_when_last_char_is_final_digit(self) -> None:
        # w is the last alphabet char; it wraps to g and carries into c -> y
        self.assertEqual(next_code("3ppscw"), "3ppsyg")
        self.assertEqual(next_code("w"), "rg")
        self.assertEqual(next_code("gw"), "rg")
        self.assertEqual(next_code("ww"), "rgg")

    def test_full_width_overflow_grows_a_digit(self) -> None:
        # w is 29; six w's are 30^6 - 1, so +1 is 1 followed by six zeros
        # with g as zero and r as one: rgggggg
        self.assertEqual(next_code("wwwwww"), "rgggggg")

    def test_rejects_empty_code(self) -> None:
        with self.assertRaises(ValueError):
            next_code("")

    def test_round_trip_integer_conversion(self) -> None:
        code = "3ppscy"
        value = code_to_int(code)
        self.assertEqual(int_to_code(value, width=len(code)), code)
        self.assertEqual(int_to_code(value + 1, width=len(code)), "3ppsc0")

    def test_rejects_unknown_character(self) -> None:
        with self.assertRaises(ValueError):
            next_code("apple")  # vowels are not in the alphabet


if __name__ == "__main__":
    unittest.main()
