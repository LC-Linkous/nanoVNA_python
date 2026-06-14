#! /usr/bin/python3
"""
Tests for the optional envelope-sourced bounds helpers (src/nvnapython/_bounds.py).

These prove the helpers are correct and ready to wire into the command mixins
once the hardware boundary probes confirm the real ranges. They also demonstrate
both candidate marker-index sourcing strategies (live sweep length vs model max)
so the eventual choice is just a call-site decision, fully covered.

No hardware required.
"""

import pytest

from nvnapython._bounds import (
    check_slot,
    check_point_count,
    check_marker_index,
    check_in_set,
)


# --- check_slot -----------------------------------------------------------

@pytest.mark.parametrize("val,num,ok", [
    (0, 5, True), (4, 5, True), (5, 5, False), (-1, 5, False),
    (0, 7, True), (6, 7, True), (7, 7, False),
])
def test_check_slot_range(val, num, ok):
    got, _ = check_slot(val, num, "save")
    assert got is ok


def test_check_slot_rejects_non_int_and_bool():
    assert check_slot("3", 5)[0] is False
    assert check_slot(True, 5)[0] is False     # bool is not a valid slot id
    assert check_slot(1.0, 5)[0] is False


# --- check_point_count: inclusive vs exclusive top ------------------------

def test_point_count_inclusive_top():
    assert check_point_count(201, 201, end_inclusive=True)[0] is True
    assert check_point_count(202, 201, end_inclusive=True)[0] is False


def test_point_count_exclusive_top():
    assert check_point_count(200, 201, end_inclusive=False)[0] is True
    assert check_point_count(201, 201, end_inclusive=False)[0] is False


def test_point_count_respects_min_floor():
    # once B1 confirms an 11-point floor, callers pass min_points=11.
    assert check_point_count(10, 201, end_inclusive=True, min_points=11)[0] is False
    assert check_point_count(11, 201, end_inclusive=True, min_points=11)[0] is True


def test_point_count_non_int():
    assert check_point_count("many", 201, end_inclusive=True)[0] is False


# --- check_marker_index: BOTH sourcing strategies -------------------------

def test_marker_index_sourced_from_live_sweep():
    # If B2 shows the device keys on CURRENT sweep points: an 11-point sweep
    # allows indices 0..10; 11 is out of range.
    sweep_len = 11
    assert check_marker_index(0, sweep_len, "current sweep")[0] is True
    assert check_marker_index(10, sweep_len, "current sweep")[0] is True
    assert check_marker_index(11, sweep_len, "current sweep")[0] is False


def test_marker_index_sourced_from_model_max():
    # If B2 shows a fixed model max instead: caller passes maxPoints as the
    # bound. Same helper, different source value.
    model_max = 201
    assert check_marker_index(200, model_max, "model max")[0] is True
    assert check_marker_index(201, model_max, "model max")[0] is False


def test_marker_index_non_int():
    assert check_marker_index("middle", 101)[0] is False


# --- check_in_set ---------------------------------------------------------

def test_check_in_set():
    assert check_in_set(3, (0, 1, 2, 3, 4, 5, 6))[0] is True
    assert check_in_set(7, (0, 1, 2, 3, 4, 5, 6))[0] is False
    assert check_in_set("in", ("load", "open", "in"))[0] is True


# --- integration sketch: helper wired against a real model envelope -------

def test_helper_against_fv2_envelope():
    # Demonstrates the intended call pattern using the actual F V2 envelope,
    # so the wiring is exercised end-to-end without touching the mixins yet.
    from nvnapython.constants import MODELS
    fv2 = MODELS["NANOVNA_F_V2"]
    ok, _ = check_point_count(fv2["max_points"], fv2["max_points"],
                              fv2["point_end_inclusive"])
    assert ok is True                                   # 201 valid (inclusive)
    # preset slots from the envelope (7) -- the value save() will eventually use
    assert check_slot(6, fv2["num_preset_slots"], "save")[0] is True
    assert check_slot(7, fv2["num_preset_slots"], "save")[0] is False
