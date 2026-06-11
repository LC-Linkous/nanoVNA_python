#! /usr/bin/python3
"""
Edge-case / behavior-pinning tests.

These pin CURRENT behavior at boundaries the README's TODO calls out as open or
potentially-changing, so that when a decision is made the change shows up as a
deliberate, visible diff to one of these tests rather than as a silent surprise.

Each test documents WHAT is pinned and WHY it's interesting; none of them
asserts that the current behavior is necessarily the final intended behavior.
"""

import pytest

from nvnapython import nanoVNA


@pytest.fixture
def rec_dev():
    """A device whose wire is a simple call-recorder (no hardware)."""
    dev = nanoVNA()
    dev.set_error_byte_return(True)
    calls = []
    dev.nanoVNA_serial = lambda *a, **k: calls.append(a[0]) or bytearray(b"")
    dev._calls = calls
    return dev


# ---------------------------------------------------------------------------
# scan(): partial point/outmask arguments
#
# scan() has two paths: (pts is None AND outmask is None) -> bare sweep; else
# the int(pts)/int(outmask) validation path. Supplying exactly ONE of them
# lands in the validation path, where int(None) raises and the method returns
# the error byte without writing. Pin that a half-specified call is rejected,
# not silently turned into a bare sweep or a malformed command.
# ---------------------------------------------------------------------------

def test_scan_pts_without_outmask_is_rejected(rec_dev):
    out = rec_dev.scan(1_000_000, 2_000_000, 101, None)
    assert rec_dev._calls == []                 # nothing sent
    assert bytes(out) == b"ERROR"


def test_scan_outmask_without_pts_is_rejected(rec_dev):
    out = rec_dev.scan(1_000_000, 2_000_000, None, 2)
    assert rec_dev._calls == []
    assert bytes(out) == b"ERROR"


# ---------------------------------------------------------------------------
# point_end_inclusive=False: scan vs marker bound DISAGREE at maxPoints.
#
# scan() honors point_end_inclusive (rejects pts == maxPoints when False), but
# marker() bounds its index with a flat 0 <= idx <= maxPoints regardless of the
# flag. So for an exclusive-top model, scan rejects N==maxPoints while marker
# still accepts idx==maxPoints. This is a real inconsistency; pin it so the
# choice to unify (or not) is explicit.
# ---------------------------------------------------------------------------

def test_exclusive_top_scan_rejects_maxpoints(rec_dev):
    rec_dev.pointEndInclusive = False
    rec_dev.maxPoints = 201
    rec_dev.scan(1_000_000, 2_000_000, 201, 2)
    assert rec_dev._calls == []                 # scan rejects pts == maxPoints


def test_exclusive_top_marker_still_accepts_maxpoints(rec_dev):
    # KNOWN INCONSISTENCY (see test above): marker() ignores point_end_inclusive
    # and accepts idx == maxPoints even when scan would reject the same count.
    rec_dev.pointEndInclusive = False
    rec_dev.maxPoints = 201
    rec_dev.marker(1, None, 201)
    assert rec_dev._calls == ["marker 1 201\r\n"]


def test_inclusive_top_scan_accepts_maxpoints(rec_dev):
    # The default F V2 model is inclusive-top, so pts == maxPoints is valid.
    rec_dev.pointEndInclusive = True
    rec_dev.maxPoints = 201
    rec_dev.scan(1_000_000, 2_000_000, 201, 2)
    assert rec_dev._calls == ["scan 1000000 2000000 201 2\r\n"]


# ---------------------------------------------------------------------------
# save vs recall slot ranges currently DISAGREE and are both HARDCODED.
#
# recall accepts 0..6 (7 slots), save accepts 0..4 (5 slots). The README TODO
# flags this against the F V2's 7 cal-storage groups and proposes reading the
# ranges from the model envelope (numCalSlots / numPresetSlots) later. Pin the
# current hardcoded edges so that future change is a visible diff -- AND pin
# that the values do not currently come from the envelope.
# ---------------------------------------------------------------------------

def test_save_upper_edge_is_four(rec_dev):
    rec_dev.save(4)
    assert rec_dev._calls == ["save 4\r\n"]


def test_save_five_currently_rejected(rec_dev):
    out = rec_dev.save(5)
    assert rec_dev._calls == []
    assert bytes(out) == b"ERROR"


def test_recall_upper_edge_is_six(rec_dev):
    rec_dev.recall(6)
    assert rec_dev._calls == ["recall 6\r\n"]


def test_recall_seven_currently_rejected(rec_dev):
    out = rec_dev.recall(7)
    assert rec_dev._calls == []
    assert bytes(out) == b"ERROR"


def test_save_recall_ranges_not_yet_envelope_driven():
    # Documents that the slot ranges are HARDCODED, not derived from the model
    # envelope: the F V2 envelope advertises 7 preset slots, but save() still
    # caps at 4. When this is wired to numPresetSlots, this test should be the
    # one that flips.
    dev = nanoVNA()                              # default F V2
    assert dev.numPresetSlots == 7               # envelope says 7
    dev.set_error_byte_return(True)
    calls = []
    dev.nanoVNA_serial = lambda *a, **k: calls.append(a[0]) or bytearray(b"")
    dev.save(5)                                  # within envelope's 7, but...
    assert calls == []                           # ...still rejected by hardcoded 0..4


# ---------------------------------------------------------------------------
# H4 model: max_points == 101, so scan bound tightens to the H4 envelope when
# that model is selected. Cross-checks the per-model seeding path end-to-end.
# ---------------------------------------------------------------------------

def test_scan_bound_follows_selected_model(rec_dev):
    rec_dev.select_existing_device("NANOVNA_H4")  # max_points 101
    rec_dev.scan(1_000_000, 2_000_000, 150, 2)    # 150 > 101 -> rejected
    assert rec_dev._calls == []
    rec_dev.scan(1_000_000, 2_000_000, 101, 2)    # exactly 101 -> accepted (incl.)
    assert rec_dev._calls == ["scan 1000000 2000000 101 2\r\n"]
