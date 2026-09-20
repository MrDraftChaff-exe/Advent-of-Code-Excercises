#!/usr/bin/env python3
"""Tests for custom-alphabet short-code incrementing."""

import unittest

from next_code import (
    DEFAULT_ALPHABET,
    apply_rotating_prefixes,
    code_to_int,
    complete_group_count,
    format_paste_groups,
    grouped,
    int_to_code,
    next_code,
    next_codes,
    parse_alphabet,
    parse_prefixes,
    previous_code,
    previous_codes,
    resolve_group_size,
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

    def test_previous_code_is_inverse_of_next(self) -> None:
        self.assertEqual(previous_code("3ppsc0"), "3ppscy")
        self.assertEqual(next_code(previous_code("3ppm3d")), "3ppm3d")
        self.assertEqual(previous_code("3ppm3d"), "3ppm3r")

    def test_previous_cannot_go_below_zero(self) -> None:
        with self.assertRaises(ValueError):
            previous_code("g")


class BatchPrefixTests(unittest.TestCase):
    def test_next_codes_starts_after_given_code(self) -> None:
        self.assertEqual(next_codes("3ppscy", 3), ["3ppsc0", "3ppscf", "3ppscj"])

    def test_rotating_prefixes_tv_tstats_tci(self) -> None:
        tagged = apply_rotating_prefixes(["3ppsc0", "3ppscf", "3ppscj", "3ppsc7"])
        self.assertEqual(
            tagged,
            ["tv 3ppsc0", "tstats 3ppscf", "tci 3ppscj", "tv 3ppsc7"],
        )

    def test_parse_prefixes(self) -> None:
        self.assertEqual(parse_prefixes("tv,tstats,tci"), ("tv", "tstats", "tci"))
        self.assertEqual(parse_prefixes(""), ())

    def test_each_group_is_one_tv_tstats_tci_set(self) -> None:
        tagged = apply_rotating_prefixes(["a", "b", "c", "d", "e", "f"])
        groups = grouped(tagged, 3)
        self.assertEqual(
            groups,
            [
                ["tv a", "tstats b", "tci c"],
                ["tv d", "tstats e", "tci f"],
            ],
        )
        self.assertEqual(
            format_paste_groups(groups),
            "tv a\ntstats b\ntci c\n\ntv d\ntstats e\ntci f",
        )

    def test_count_rounds_up_to_complete_prefix_sets(self) -> None:
        self.assertEqual(complete_group_count(1000, 3), 1002)
        self.assertEqual(complete_group_count(999, 3), 999)
        self.assertEqual(complete_group_count(1000, 2), 1000)

    def test_groups_of_two(self) -> None:
        tagged = apply_rotating_prefixes(["a", "b", "c", "d"])
        groups = grouped(tagged, 2)
        self.assertEqual(
            groups,
            [
                ["tv a", "tstats b"],
                ["tci c", "tv d"],
            ],
        )
        self.assertEqual(
            format_paste_groups(groups),
            "tv a\ntstats b\n\ntci c\ntv d",
        )
        self.assertEqual(resolve_group_size(("tv", "tstats", "tci"), 2, 1000), 2)
        self.assertEqual(resolve_group_size(("tv", "tstats", "tci"), None, 1000), 3)

    def test_previous_codes_from_3ppm3d(self) -> None:
        self.assertEqual(previous_codes("3ppm3d", 3), ["3ppm3r", "3ppm3g", "3ppmqw"])


if __name__ == "__main__":
    unittest.main()
