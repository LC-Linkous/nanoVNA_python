#! /usr/bin/python3
"""
Command-construction tests for the MarkersTracesMixin.

Mocked-serial `nvna` fixture; no hardware. The marker() tests are the key ones:
the original code raised TypeError on every marker SET (str + +'\\r\\n'), so the
happy-path asserts below would all have failed against the old library.
"""

import pytest


# --- marker: dump / position / index / action ----------------------------

def test_marker_dump_all(nvna):
    nvna.marker()
    assert nvna._recorder.last == "marker\r\n"


def test_marker_dump_one(nvna):
    nvna.get_marker_position(2)
    assert nvna._recorder.last == "marker 2\r\n"


def test_marker_set_index(nvna):
    # FIXED: original 'marker '+ID+' '+idx + +'\r\n' raised TypeError.
    nvna.set_marker_position(1, 50)
    assert nvna._recorder.last == "marker 1 50\r\n"


@pytest.mark.parametrize("method,word", [
    ("marker_on", "on"),
    ("marker_off", "off"),
    ("marker_peak", "peak"),
])
def test_marker_action_aliases(nvna, method, word):
    # FIXED: every action branch raised TypeError on str + +'\r\n'.
    getattr(nvna, method)(1)
    assert nvna._recorder.last == f"marker 1 {word}\r\n"


@pytest.mark.parametrize("bad_id", [0, 5, None, "x"])
def test_marker_bad_id(nvna, bad_id):
    nvna.marker(bad_id, "on")
    assert nvna._recorder.count == 0


def test_marker_bad_action(nvna):
    nvna.marker(1, "explode")
    assert nvna._recorder.count == 0


# --- trace: dump / per-trace / format / format+value ----------------------

def test_trace_dump_all(nvna):
    nvna.get_all_trace_attr()
    assert nvna._recorder.last == "trace\r\n"


def test_trace_dump_one(nvna):
    nvna.get_trace_attr(1)
    assert nvna._recorder.last == "trace 1\r\n"


def test_trace_dump_all_keyword(nvna):
    nvna.trace("all")
    assert nvna._recorder.last == "trace all\r\n"


@pytest.mark.parametrize("method,fmt", [
    ("trace_off", "off"),
    ("set_trace_logmag", "logmag"),
    ("set_trace_linear", "linear"),
    ("set_trace_phase", "phase"),
    ("set_trace_smith", "smith"),
    ("set_trace_polar", "polar"),
])
def test_trace_format_aliases(nvna, method, fmt):
    getattr(nvna, method)(1)
    assert nvna._recorder.last == f"trace 1 {fmt}\r\n"


@pytest.mark.parametrize("method,fmt,val", [
    ("set_trace_swr", "swr", 2),
    ("set_trace_refposition", "refpos", 5),
    ("set_trace_delay", "delay", 10),
])
def test_trace_format_value_aliases(nvna, method, fmt, val):
    getattr(nvna, method)(1, val)
    assert nvna._recorder.last == f"trace 1 {fmt} {val}\r\n"


def test_trace_channel_valid(nvna):
    nvna.set_trace_channel(1, 0)
    assert nvna._recorder.last == "trace 1 channel 0\r\n"


def test_trace_channel_invalid(nvna):
    nvna.set_trace_channel(1, "S21")
    assert nvna._recorder.count == 0


def test_trace_bad_id(nvna):
    nvna.trace(9, "logmag")
    assert nvna._recorder.count == 0


def test_trace_bad_format(nvna):
    nvna.trace(1, "rainbow")
    assert nvna._recorder.count == 0


def test_marker_set_index_non_int(nvna):
    # ID valid, idx present but non-integer -> error path, no serial write.
    nvna.set_marker_position(1, "middle")
    assert nvna._recorder.count == 0


# --- marker index bound (0..maxPoints) ------------------------------------

def test_marker_set_index_in_bounds(nvna):
    nvna.set_marker_position(1, 0)
    assert nvna._recorder.last == "marker 1 0\r\n"


def test_marker_set_index_out_of_bounds(nvna):
    # maxPoints seeded at 201; an index well past it is rejected.
    nvna.set_marker_position(1, 5000)
    assert nvna._recorder.count == 0
