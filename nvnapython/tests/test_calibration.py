#! /usr/bin/python3
"""
Command-construction tests for the CalibrationMixin.

Mocked-serial `nvna` fixture; no hardware. Covers the SOLT cal flow and edelay.
"""

import pytest


# --- cal: load|open|short|thru|done|reset|on|off --------------------------

@pytest.mark.parametrize("val", [
    "load", "open", "short", "thru", "done", "reset", "on", "off",
])
def test_cal_valid(nvna, val):
    nvna.cal(val)
    assert nvna._recorder.last == f"cal {val}\r\n"


def test_cal_invalid(nvna):
    nvna.cal("calibrate_everything")
    assert nvna._recorder.count == 0


@pytest.mark.parametrize("method,val", [
    ("cal_load", "load"),
    ("cal_open", "open"),
    ("cal_short", "short"),
    ("cal_thru", "thru"),
    ("cal_done", "done"),
    ("cal_reset", "reset"),
    ("cal_on", "on"),
    ("cal_off", "off"),
])
def test_cal_aliases(nvna, method, val):
    # FIXED: cal_off() previously sent 'cal of' (typo) instead of 'cal off'.
    getattr(nvna, method)()
    assert nvna._recorder.last == f"cal {val}\r\n"


# --- edelay: None (get) or numeric (set) ----------------------------------

def test_edelay_get(nvna):
    nvna.get_edelay()
    assert nvna._recorder.last == "edelay\r\n"


def test_edelay_set_int(nvna):
    nvna.set_edelay(5)
    assert nvna._recorder.last == "edelay 5\r\n"


def test_edelay_set_float(nvna):
    nvna.edelay(1.5e-9)
    assert nvna._recorder.last == "edelay 1.5e-09\r\n"


def test_edelay_set_invalid(nvna):
    nvna.edelay("soon")
    assert nvna._recorder.count == 0


# --- cal in: documented, no-op on F V2, accepted as pass-through ----------

def test_cal_in_valid(nvna):
    nvna.cal("in")
    assert nvna._recorder.last == "cal in\r\n"


def test_cal_in_alias(nvna):
    nvna.cal_in()
    assert nvna._recorder.last == "cal in\r\n"
