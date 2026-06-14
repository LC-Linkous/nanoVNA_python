#! /usr/bin/python3
"""
Command-construction tests for the SystemInfoMixin.

Mocked-serial `nvna` fixture; no hardware.
"""

import pytest


# --- fixed-string getters -------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("info", "info\r\n"),
    ("get_info", "info\r\n"),
    ("SN", "SN\r\n"),
    ("get_SN", "SN\r\n"),
    ("version", "version\r\n"),
    ("get_version", "version\r\n"),
    ("nanoVNA_help", "help\r\n"),
])
def test_fixed_string_getters(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


# --- command(): passthrough -----------------------------------------------

def test_command_passthrough(nvna):
    nvna.command("scan 150000 250000000 200 2")
    assert nvna._recorder.last == "scan 150000 250000000 200 2\r\n"


# --- help() routing -------------------------------------------------------

def test_help_routes_to_device(nvna):
    # val != 1 -> nanoVNA_help() -> sends 'help\r\n'
    nvna.help(0)
    assert nvna._recorder.last == "help\r\n"


def test_help_library_no_serial(nvna):
    # val == 1 -> library_help() -> returns b'' without touching serial
    out = nvna.help(1)
    assert nvna._recorder.count == 0
    assert out == b""


# --- NanoVNA_Help: README-named alias for nanoVNA_help --------------------

def test_NanoVNA_Help_alias(nvna):
    nvna.NanoVNA_Help()
    assert nvna._recorder.last == "help\r\n"
