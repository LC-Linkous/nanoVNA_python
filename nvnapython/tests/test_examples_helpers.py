#! /usr/bin/python3
"""
Tests for examples/_helpers.py.

The examples are part of what users copy, so their shared parsing helpers
deserve the same regression protection as the library. These run the helpers
against the SAME verbatim hardware captures used in test_hardware_captures.py.
No hardware required.
"""

import os
import sys
import math
import pytest

# make examples/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))

from _helpers import (   # noqa: E402
    convert_s11_data_to_arrays,
    convert_frequencies_to_array,
    convert_scan_outmask7_to_arrays,
    complex_to_db,
)


def test_s11_pairs_from_real_scan_capture():
    # outmask 2 capture: "re im " per line with a trailing space.
    raw = (b"1.097607 1.186987 \r\n1.155769 1.300400 \r\n2.108881 1.318900 \r\n"
           b"ch> \r\nch> ")
    reals, imags = convert_s11_data_to_arrays(raw)
    assert reals == [1.097607, 1.155769, 2.108881]
    assert imags == [1.186987, 1.300400, 1.318900]


def test_s11_skips_prompt_and_blank_lines():
    raw = b"1.0 0.0 \r\n\r\n0.5 -0.5 \r\nch> \r\nch> "
    reals, imags = convert_s11_data_to_arrays(raw)
    assert reals == [1.0, 0.5]
    assert imags == [0.0, -0.5]


def test_frequencies_parse():
    raw = b"1000000\r\n1100000\r\n2000000\r\nch> \r\nch> "
    assert convert_frequencies_to_array(raw) == [1_000_000, 1_100_000, 2_000_000]


def test_frequencies_handles_trailing_space_scan_variant():
    # scan outmask 1 lines carry a trailing space; should still parse to ints.
    raw = b"1000000 \r\n1100000 \r\n2000000 \r\nch> \r\nch> "
    assert convert_frequencies_to_array(raw) == [1_000_000, 1_100_000, 2_000_000]


def test_outmask7_five_columns():
    raw = (b"1000000 1.098258 1.188245 -0.000036 0.000027 \r\n"
           b"1100000 1.153075 1.299057 -0.000010 0.000002 \r\nch> \r\nch> ")
    f, s11r, s11i, s21r, s21i = convert_scan_outmask7_to_arrays(raw)
    assert f == [1_000_000, 1_100_000]
    assert s11r == [1.098258, 1.153075]
    assert s21i == [0.000027, 0.000002]


def test_complex_to_db_values():
    # |1+0j| = 1 -> 0 dB; |0.5+0j| = 0.5 -> ~ -6.02 dB
    db = complex_to_db([1.0, 0.5], [0.0, 0.0])
    assert abs(db[0]) < 1e-9
    assert abs(db[1] - (20 * math.log10(0.5))) < 1e-9


def test_complex_to_db_zero_magnitude_is_floored():
    # a zero sample must not raise (log10(0)); it floors instead.
    db = complex_to_db([0.0], [0.0])
    assert db == [-200.0]


def test_helpers_accept_str_and_bytes():
    # convenience: helpers tolerate str input as well as bytes.
    reals, imags = convert_s11_data_to_arrays("1.0 2.0\r\n3.0 4.0\r\n")
    assert reals == [1.0, 3.0] and imags == [2.0, 4.0]
