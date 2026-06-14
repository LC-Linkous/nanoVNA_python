#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/test_hardware_probe.py'
#
#   HARDWARE PROBES for open questions about the real device envelope.
#
#   Unlike test_hardware.py (which asserts known-good behavior), these tests
#   probe things the docs disagree about or that were only ever seen on one
#   device / one firmware. Each probe PRINTS what the device actually returned
#   so we can read the true behavior off the captured output, then tighten the
#   library + constants.py to match.
#
#   Run with output visible (the -s flag is the point of these tests):
#
#       pytest -m hardware tests/test_hardware_probe.py -s -v
#
#   These are intentionally tolerant: a probe should FAIL only if the device
#   errored in a way that tells us something, not merely because a value
#   differed from a guess. Read the printed REPORT lines.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import time
import pytest

pytestmark = pytest.mark.hardware


# ---------------------------------------------------------------------------
# Session-scoped device: connect ONCE, reuse across all probes, disconnect at
# the end. Per-test connect/disconnect was causing enumeration races (skips);
# one connection for the whole session avoids hammering the port.
# ---------------------------------------------------------------------------

def _decode(b):
    """bytes/bytearray -> str for printing, tolerant of None/empty."""
    if not b:
        return ""
    try:
        return bytes(b).decode("utf-8", errors="replace").strip()
    except Exception:
        return repr(b)


def _looks_like_error(b):
    """Heuristic: did the device reject the command?"""
    s = _decode(b).lower()
    return (b == bytearray(b"ERROR")) or ("not recognised" in s) or \
           ("not recognized" in s) or ("error" in s) or ("usage" in s)


def _drain(device, settle=0.15):
    """Settle the device and clear any stale bytes from the input buffer.

    Some commands -- especially ones this firmware does NOT recognise (e.g.
    'port') -- can respond slowly or leave the console output partially drained.
    On the SHARED module-scoped connection these probes use, that residue can
    race the NEXT command's read: reset_input_buffer() + write happen before the
    stale reply has fully arrived, so get_serial_return() can return the leftover
    tail (or nothing) instead of the new command's output. This was the cause of
    the intermittent empty 'help' dump -- 'help' itself reads cleanly in
    isolation (see diagnose_help.py), it was the preceding 'port' probe leaving
    the port dirty.

    Call this after any probe that sends a command expected to error/be
    unrecognised, and as a guard before a large read on the shared connection.
    """
    time.sleep(settle)
    try:
        if device.ser is not None:
            device.ser.reset_input_buffer()
    except Exception:
        pass


# ===========================================================================
# QUESTION 1: scan points. README says "51-201, end not inclusive". The
# Chelegance F V2 user guide says "11-201 configurable". Which is true?
# We probe the boundaries on the real device.
# ===========================================================================

@pytest.mark.parametrize("pts", [11, 51, 101, 200, 201])
def test_probe_scan_points_accepted(device, pts):
    """
    Probe which point counts the device actually accepts. We send via the
    passthrough command() so the LIBRARY's own bounds don't filter the test --
    we want the DEVICE's verdict, not the library's.
    """
    device.pause()
    raw = device.command(f"scan 1000000 2000000 {pts} 2")
    pairs = [ln for ln in _decode(raw).split("\n") if ln.strip()]
    print(f"\n  [REPORT] scan pts={pts}: returned {len(pairs)} lines, "
          f"error={_looks_like_error(raw)}")
    if pairs[:1]:
        print(f"           first line: {pairs[0]!r}")
    # Only fail if the device explicitly errored. A short/long count is data,
    # not a failure -- we want to SEE it.
    assert not _looks_like_error(raw), \
        f"device rejected pts={pts}: {_decode(raw)[:120]}"
    device.resume()


def test_probe_scan_points_over_max(device):
    """
    What does the device do at 202 and beyond? Does it clamp, error, or accept?
    This tells us whether maxPoints should be a hard reject or a clamp.
    """
    device.pause()
    for pts in (202, 256, 401):
        raw = device.command(f"scan 1000000 2000000 {pts} 2")
        pairs = [ln for ln in _decode(raw).split("\n") if ln.strip()]
        print(f"\n  [REPORT] scan pts={pts}: returned {len(pairs)} lines, "
              f"error={_looks_like_error(raw)}, "
              f"sample={_decode(raw)[:60]!r}")
    device.resume()
    # no assertion: this is purely informational about over-limit behavior


# ===========================================================================
# QUESTION 2: cal / preset slot counts. The F V2 guide says 7 calibration
# storage groups; the library's recall accepts 0-6 and save accepts 0-4.
# Probe what recall/save actually accept WITHOUT writing anything destructive:
# we only test RECALL (load), never save, to avoid clobbering the user's cals.
# ===========================================================================

@pytest.mark.parametrize("slot", [0, 1, 2, 3, 4, 5, 6])
def test_probe_recall_slots(device, slot):
    """
    Probe which recall slots the device accepts. recall is non-destructive
    (it LOADS a stored state); we restore by recalling slot 0 afterward.
    NOTE: this changes the active state on the device but writes nothing.
    """
    raw = device.command(f"recall {slot}")
    print(f"\n  [REPORT] recall {slot}: error={_looks_like_error(raw)}, "
          f"resp={_decode(raw)[:80]!r}")
    # informational; we don't assert a hard range since we're learning it
    # restore to startup preset
    device.command("recall 0")


# ===========================================================================
# QUESTION 3: the 'data N' table. Library accepts 0-6 (S11, S21, then cal
# tables). Probe which indices return data vs error on this firmware.
# ===========================================================================

@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5, 6])
def test_probe_data_indices(device, n):
    device.pause()
    raw = device.command(f"data {n}")
    lines = [ln for ln in _decode(raw).split("\n") if ln.strip()]
    print(f"\n  [REPORT] data {n}: {len(lines)} lines, "
          f"error={_looks_like_error(raw)}, first={lines[0] if lines else ''!r}")
    device.resume()


# ===========================================================================
# QUESTION 4: does this firmware accept 'cal in'? The README says it's
# documented but has no button on the F V2. Probe whether it errors.
# ===========================================================================

def test_probe_cal_in(device):
    raw = device.command("cal in")
    print(f"\n  [REPORT] 'cal in': error={_looks_like_error(raw)}, "
          f"resp={_decode(raw)[:80]!r}")
    # informational -- tells us whether to keep accepting 'in' in cal()


# ===========================================================================
# QUESTION 5: does 'port' exist on this firmware? It appears in the help dump
# but has no command section. Probe port 1 / port 2.
# ===========================================================================

@pytest.mark.parametrize("p", [1, 2])
def test_probe_port(device, p):
    raw = device.command(f"port {p}")
    print(f"\n  [REPORT] 'port {p}': error={_looks_like_error(raw)}, "
          f"resp={_decode(raw)[:80]!r}")
    # 'port' is not a real command on this firmware; it can leave the console
    # output partially drained. Settle + flush so the next probe on the shared
    # connection starts from a clean buffer.
    _drain(device)


# ===========================================================================
# QUESTION 7: confirm the trailing-space S11 format and that 201 points
# returns 201 pairs (not 200, not 202) -- the off-by-one / inclusivity check.
# ===========================================================================

def test_probe_201_returns_201_pairs(device):
    device.pause()
    raw = device.command("scan 1000000 2000000 201 2")
    pairs = [ln for ln in _decode(raw).split("\n") if ln.strip()]
    print(f"\n  [REPORT] scan 201 pts -> {len(pairs)} S11 pairs returned")
    if pairs:
        print(f"           first: {pairs[0]!r}")
        print(f"           last:  {pairs[-1]!r}")
        # verify each line parses as a real/imag pair
        sample = pairs[0].split()
        print(f"           values per line: {len(sample)}")
    device.resume()
    assert not _looks_like_error(raw), "device errored on 201-point scan"
    # report the count rather than hard-asserting 201 -- we want to LEARN it
    print(f"  [REPORT] CONCLUSION: device returned {len(pairs)} pairs for 201 requested")