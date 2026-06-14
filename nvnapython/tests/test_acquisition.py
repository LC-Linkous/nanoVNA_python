#! /usr/bin/python3
"""
Command-construction tests for the AcquisitionMixin.

Mocked-serial `nvna` fixture; no hardware. Covers data (S11/S21/cal),
frequencies, scan (+ outmask aliases, pts bounded by seeded maxPoints=201),
config_sweep + aliases, run_sweep, cwfreq, pause/resume.
"""

import pytest


# --- data: 0..6 -----------------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("get_s11_data", "data 0\r\n"),
    ("get_s21_data", "data 1\r\n"),
    ("get_load_cal_data", "data 2\r\n"),
    ("get_open_cal_data", "data 3\r\n"),
    ("get_short_cal_data", "data 4\r\n"),
    ("get_thru_cal_data", "data 5\r\n"),
    ("get_isolation_cal_data", "data 6\r\n"),
])
def test_data_aliases(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


def test_data_invalid(nvna):
    nvna.data(7)
    assert nvna._recorder.count == 0


# --- frequencies ----------------------------------------------------------

def test_frequencies(nvna):
    nvna.frequencies()
    assert nvna._recorder.last == "frequencies\r\n"


def test_get_last_freqs_alias(nvna):
    nvna.get_last_freqs()
    assert nvna._recorder.last == "frequencies\r\n"


# --- pause / resume -------------------------------------------------------

@pytest.mark.parametrize("method,expected", [
    ("pause", "pause\r\n"),
    ("resume", "resume\r\n"),
])
def test_pause_resume(nvna, method, expected):
    getattr(nvna, method)()
    assert nvna._recorder.last == expected


# --- cwfreq ---------------------------------------------------------------

def test_cwfreq_valid(nvna):
    # FIXED: original built 'cwfreq'+val with no space ('cwfreq150000000').
    nvna.cwfreq(150_000_000)
    assert nvna._recorder.last == "cwfreq 150000000\r\n"


def test_cwfreq_float_valid(nvna):
    # FIXED: original rejected floats (isinstance int gate after int(val)).
    nvna.set_cwfreq(1.5e9)
    assert nvna._recorder.last == "cwfreq 1500000000.0\r\n"


def test_cwfreq_invalid(nvna):
    nvna.cwfreq("a lot")
    assert nvna._recorder.count == 0


# --- scan: start<stop, pts>0 and <=maxPoints, outmask 0..7 ----------------

def test_scan_no_pts_no_outmask(nvna):
    nvna.scan(1_000_000, 2_000_000)
    assert nvna._recorder.last == "scan 1000000 2000000\r\n"


def test_scan_full(nvna):
    nvna.scan(1_000_000, 2_000_000, 101, 2)
    assert nvna._recorder.last == "scan 1000000 2000000 101 2\r\n"


@pytest.mark.parametrize("method,outmask", [
    ("get_scan_frequencies", 1),
    ("get_scan_s11", 2),
    ("get_scan_freqs_s11", 3),
    ("get_scan_s21", 4),
    ("get_scan_freqs_s21", 5),
    ("get_scan_s11_s21", 6),
    ("get_scan_freqs_s11_s21", 7),
])
def test_scan_outmask_aliases(nvna, method, outmask):
    getattr(nvna, method)(1_000_000, 2_000_000, 101)
    assert nvna._recorder.last == f"scan 1000000 2000000 101 {outmask}\r\n"


def test_scan_range_alias(nvna):
    nvna.scan_range(1_000_000, 2_000_000)
    assert nvna._recorder.last == "scan 1000000 2000000\r\n"


@pytest.mark.parametrize("start,stop,pts,outmask", [
    (2_000_000, 1_000_000, 101, 2),   # start >= stop
    ("x", 2_000_000, 101, 2),          # non-numeric start
    (1_000_000, 2_000_000, 0, 2),      # pts <= 0
    (1_000_000, 2_000_000, 999, 2),    # pts > maxPoints (201)
    (1_000_000, 2_000_000, 101, 9),    # outmask out of 0..7
])
def test_scan_invalid(nvna, start, stop, pts, outmask):
    nvna.scan(start, stop, pts, outmask)
    assert nvna._recorder.count == 0


# --- config_sweep + aliases -----------------------------------------------

def test_config_sweep_dump(nvna):
    nvna.get_sweep_params()
    assert nvna._recorder.last == "sweep\r\n"


@pytest.mark.parametrize("method,val,expected", [
    ("set_sweep_start", 100e6, "sweep start 100000000.0\r\n"),
    ("set_sweep_stop", 200e6, "sweep stop 200000000.0\r\n"),
    ("set_sweep_center", 150e6, "sweep center 150000000.0\r\n"),
    ("set_sweep_span", 50e6, "sweep span 50000000.0\r\n"),
    ("set_sweep_cw", 150e6, "sweep cw 150000000.0\r\n"),
])
def test_config_sweep_aliases(nvna, method, val, expected):
    getattr(nvna, method)(val)
    assert nvna._recorder.last == expected


def test_config_sweep_bad_arg(nvna):
    nvna.config_sweep("bogus", 100)
    assert nvna._recorder.count == 0


def test_config_sweep_arg_without_value(nvna):
    nvna.config_sweep("start", None)
    assert nvna._recorder.count == 0


# --- run_sweep ------------------------------------------------------------

def test_run_sweep_valid(nvna):
    # FIXED: original appended a stray '1' after pts ('...'+str(pts)+'1\r\n').
    nvna.run_sweep(100e6, 200e6, 250)
    assert nvna._recorder.last == "sweep 100000000.0 200000000.0 250\r\n"


@pytest.mark.parametrize("start,stop", [
    (None, 200e6),
    (200e6, 100e6),    # start >= stop
])
def test_run_sweep_invalid(nvna, start, stop):
    nvna.run_sweep(start, stop)
    assert nvna._recorder.count == 0


def test_scan_non_int_pts(nvna):
    # pts not int-able with an outmask present -> error path, no serial write.
    nvna.scan(1_000_000, 2_000_000, "many", 2)
    assert nvna._recorder.count == 0


# --- scan pts boundary: 201 exclusive (README: "range 51 -201", end not incl.) ---

def test_scan_pts_200_accepted(nvna):
    nvna.scan(1_000_000, 2_000_000, 200, 2)
    assert nvna._recorder.last == "scan 1000000 2000000 200 2\r\n"


def test_scan_pts_201_accepted(nvna):
    # The Chelegance F V2 user guide lists sweep points as "201 / 11-201
    # configurable", so 201 (== maxPoints) IS a valid count for this model.
    nvna.scan(1_000_000, 2_000_000, 201, 2)
    assert nvna._recorder.last == "scan 1000000 2000000 201 2\r\n"


def test_scan_pts_over_max_rejected(nvna):
    # one past the model's maxPoints is rejected
    nvna.scan(1_000_000, 2_000_000, 202, 2)
    assert nvna._recorder.count == 0


# --- preform_sweep: alias for run_sweep (README prose name) ---------------

def test_preform_sweep_valid(nvna):
    nvna.preform_sweep(100e6, 200e6, 250)
    assert nvna._recorder.last == "sweep 100000000.0 200000000.0 250\r\n"
