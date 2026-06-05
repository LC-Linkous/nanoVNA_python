#! /usr/bin/python3
"""
Command-construction tests for the PresetsConfigMixin.

Mocked-serial `nvna` fixture; no hardware. NOTE: reset/clear_config would be
destructive on a real device, but here nanoVNA_serial is the recorder, so these
only assert the command string is built correctly -- nothing is sent to hardware.
"""

import pytest


# --- recall: 0..6 ---------------------------------------------------------

@pytest.mark.parametrize("val", [0, 1, 2, 3, 4, 5, 6])
def test_recall_valid(nvna, val):
    nvna.recall(val)
    assert nvna._recorder.last == f"recall {val}\r\n"


@pytest.mark.parametrize("val", [7, -1, "x"])
def test_recall_invalid(nvna, val):
    nvna.recall(val)
    assert nvna._recorder.count == 0


# --- save: 0..4 -----------------------------------------------------------

@pytest.mark.parametrize("val", [0, 1, 2, 3, 4])
def test_save_valid(nvna, val):
    nvna.save(val)
    assert nvna._recorder.last == f"save {val}\r\n"


@pytest.mark.parametrize("val", [5, -1, "x"])
def test_save_invalid(nvna, val):
    nvna.save(val)
    assert nvna._recorder.count == 0


# --- fixed-string config commands -----------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("save_config", "saveconfig\r\n"),
    ("clear_config", "clearconfig 1234\r\n"),
    ("reset", "reset\r\n"),
    ("reset_device", "reset\r\n"),
])
def test_fixed_string_commands(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


# --- clear_and_reset: clearconfig then reset, must not raise --------------

def test_clear_and_reset_sends_both_and_survives(nvna):
    # On REAL hardware reset() drops the serial and may raise/hang, so
    # clear_and_reset catches exceptions and must not propagate them. The mock
    # can't simulate the disconnect; this verifies both commands are sent in
    # order and no exception escapes.
    out = nvna.clear_and_reset()              # must not raise
    assert nvna._recorder.calls[0] == "clearconfig 1234\r\n"
    assert nvna._recorder.calls[1] == "reset\r\n"
    # return value intentionally not asserted (None or msgbytes depending on
    # whether the port dropped before a response arrived).
    _ = out


# --- restart: 0 (cancel) or positive seconds ------------------------------

def test_restart_cancel(nvna):
    nvna.cancel_restart()
    assert nvna._recorder.last == "restart 0\r\n"


def test_restart_seconds(nvna):
    nvna.restart_device(5)
    assert nvna._recorder.last == "restart 5\r\n"


def test_restart_direct_zero(nvna):
    nvna.restart(0)
    assert nvna._recorder.last == "restart 0\r\n"


@pytest.mark.parametrize("val", [-1, "soon"])
def test_restart_invalid(nvna, val):
    nvna.restart(val)
    assert nvna._recorder.count == 0
