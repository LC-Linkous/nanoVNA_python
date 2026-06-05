#! /usr/bin/python3
"""
Parsing / response-cleaning tests.

These exercise the REAL parsing helpers (clean_return, get_serial_return) and
the color validators against canned device-style bytes. No hardware required.
"""

import pytest


# ---------------------------------------------------------------------------
# clean_return: strips the echoed command + first \r\n from the front,
#               and a trailing 'ch>' from the end.
# ---------------------------------------------------------------------------

def test_clean_return_strips_command_and_prompt(parsing_nvna):
    raw = bytearray(b"info\r\nModel: NanoVNA-F_V2\r\nch>")
    assert parsing_nvna.clean_return(raw) == bytearray(b"Model: NanoVNA-F_V2\r")


def test_clean_return_no_chevron_left_intact(parsing_nvna):
    raw = bytearray(b"cmd\r\nPAYLOAD\r")
    assert parsing_nvna.clean_return(raw) == bytearray(b"PAYLOAD\r")


def test_clean_return_s11_pairs(parsing_nvna):
    # S11 scan output: whitespace-separated real/imag pairs, one per line.
    raw = bytearray(b"scan 1000000 2000000 2 2\r\n1.0 0.0\r\n0.5 -0.5\r\nch>")
    assert parsing_nvna.clean_return(raw) == bytearray(b"1.0 0.0\r\n0.5 -0.5\r")


# ---------------------------------------------------------------------------
# get_serial_return: reads up to the 'ch>' prompt.
# ---------------------------------------------------------------------------

def test_get_serial_return_reads_to_prompt(parsing_nvna):
    parsing_nvna.ser._buf = b"info\r\nModel: NanoVNA-F_V2\r\nch>"
    out = parsing_nvna.get_serial_return()
    assert out.endswith(b">")
    assert b"NanoVNA-F_V2" in out


# ---------------------------------------------------------------------------
# is_rgb24: 0xRRGGBB validator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s,ok", [
    ("0xFF8800", True),
    ("0x000000", True),
    ("0xffffff", True),
    ("0xFF88", False),
    ("FF8800", False),
    ("0xGG8800", False),
])
def test_is_rgb24(parsing_nvna, s, ok):
    assert parsing_nvna.is_rgb24(s) is ok


# ---------------------------------------------------------------------------
# is_rgb565_hex: 4-digit RGB565 validator (used by lcd())
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s,ok", [
    ("F800", True),
    ("0xF800", True),
    ("07e0", True),
    ("F80", False),     # too short
    ("F8000", False),   # too long
    ("GGGG", False),    # non-hex
])
def test_is_rgb565_hex(parsing_nvna, s, ok):
    assert parsing_nvna.is_rgb565_hex(s) is ok


# ---------------------------------------------------------------------------
# error_byte_return: toggled by set_error_byte_return
# ---------------------------------------------------------------------------

def test_error_byte_default_empty(parsing_nvna):
    parsing_nvna.set_error_byte_return(False)
    assert parsing_nvna.error_byte_return() == bytearray(b"")


def test_error_byte_explicit(parsing_nvna):
    parsing_nvna.set_error_byte_return(True)
    assert parsing_nvna.error_byte_return() == bytearray(b"ERROR")
