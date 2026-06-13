#! /usr/bin/python3

##------------------------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './tests/test_hardware_audit.py'
#
#   HARDWARE AUDIT probes -- round 2. Two jobs:
#
#   1. Confirm the REAL scan()/data() methods (not raw command() passthrough)
#      return exactly the expected number of clean S11 pairs, so we know
#      clean_return handles the largest frame without dropping/mangling.
#
#   2. Phantom hunt: test the commands the library BUILDS but the device 'help'
#      dump does NOT list, to decide keep / remove / document-as-unlisted.
#      From the static audit, the only such command is 'restart'. We also
#      re-confirm 'cal in' (works but is unlisted) so both unlisted commands
#      are settled in one run.
#
#   Run with output visible:
#       pytest -m hardware tests/test_hardware_audit.py -s -v
#
#   SAFETY: non-destructive. We do NOT call save (no writes). 'restart 0' is
#   the cancel form (cancels a pending restart) and is the safe way to probe
#   whether the command exists without actually rebooting the device.
#
#   Author(s): Lauren Linkous
##--------------------------------------------------------------------------------------------------\

import pytest

pytestmark = pytest.mark.hardware


def _decode(b):
    if not b:
        return ""
    try:
        return bytes(b).decode("utf-8", errors="replace").strip()
    except Exception:
        return repr(b)


def _looks_like_error(b):
    s = _decode(b).lower()
    return (b == bytearray(b"ERROR")) or ("not recognised" in s) or \
           ("not recognized" in s) or ("usage" in s) or ("exceeds" in s)


def _pairs(b):
    """Parse the cleaned device text into [real, imag] float pairs."""
    out = []
    for ln in _decode(b).split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split()
        if len(parts) >= 2:
            try:
                out.append((float(parts[0]), float(parts[1])))
            except ValueError:
                pass  # skip any framing line that isn't numbers
    return out


# ===========================================================================
# JOB 1: real scan()/data() return the right number of clean pairs.
# Uses the LIBRARY methods (clean_return applied), not raw command().
# ===========================================================================

@pytest.mark.parametrize("pts", [11, 101, 201])
def test_scan_method_returns_clean_pairs(device, pts):
    device.pause()
    raw = device.get_scan_s11(int(1e9), int(2e9), pts)   # outmask 2, real method
    pairs = _pairs(raw)
    print(f"\n  [REPORT] get_scan_s11 pts={pts}: parsed {len(pairs)} clean pairs "
          f"(expected {pts})")
    if pairs:
        print(f"           first={pairs[0]} last={pairs[-1]}")
    device.resume()
    # the real method should yield exactly pts pairs with no framing junk
    assert not _looks_like_error(raw), f"scan errored: {_decode(raw)[:120]}"
    assert len(pairs) == pts, \
        f"expected {pts} pairs from scan(), got {len(pairs)} -- clean_return may be off"


def test_data_s11_returns_clean_pairs(device):
    device.pause()
    raw = device.get_s11_data()           # data 0, real method
    pairs = _pairs(raw)
    print(f"\n  [REPORT] get_s11_data: parsed {len(pairs)} clean pairs")
    if pairs:
        print(f"           first={pairs[0]} last={pairs[-1]}")
    device.resume()
    assert not _looks_like_error(raw)
    assert len(pairs) > 0, "data 0 returned no parseable pairs"


# ===========================================================================
# JOB 2: phantom hunt -- commands the library builds but the help dump omits.
# ===========================================================================

def test_restart_exists_or_phantom(device):
    """
    'restart' is in the library (from the README) but NOT in the device help
    dump. Probe with the SAFE cancel form 'restart 0' (cancels a pending
    restart; does not reboot). If the device says 'Command not recognised',
    restart is a phantom like 'port' was and should be removed.
    """
    raw = device.command("restart 0")
    err = _looks_like_error(raw)
    print(f"\n  [REPORT] 'restart 0': error={err}, resp={_decode(raw)[:100]!r}")
    print(f"  [REPORT] CONCLUSION: restart is "
          f"{'A PHANTOM (remove it)' if err else 'REAL (keep it)'}")
    # informational -- no hard assert; the printed conclusion drives the decision


def test_cal_in_unlisted_but_works(device):
    """
    Re-confirm 'cal in' -- works on firmware but is not in the help dump's
    'cal [load|open|short|thru|done|reset|on|off]'. Settles whether to keep it
    as a documented-unlisted action.
    """
    raw = device.command("cal in")
    err = _looks_like_error(raw)
    print(f"\n  [REPORT] 'cal in': error={err}, resp={_decode(raw)[:100]!r}")
    print(f"  [REPORT] CONCLUSION: cal in is "
          f"{'NOT accepted (drop from cal actions)' if err else 'accepted (keep, mark unlisted)'}")


# ===========================================================================
# JOB 3: re-capture help dump as a stored reference (so the README reconcile
# has the authoritative list committed alongside the audit results).
# ===========================================================================

def test_capture_help_reference(device):
    raw = device.command("help")
    print("\n  [REPORT] ===== authoritative help dump =====")
    print(_decode(raw))
    print("  [REPORT] ===== end =====")
    assert raw


# ===========================================================================
# QUESTION: cwfreq units. The help dump says {frequency(Hz)} but the bare
# 'cwfreq' usage string says {frequency(KHz)}. Settle which the device acts on.
#
# Approach: set cwfreq to 100000, then read the sweep state. If the device
# treated it as Hz, the CW point is 100 kHz; if kHz, it's 100 MHz. We read back
# via 'sweep' (which reports start/stop/points) after putting the device in CW
# mode with 'sweep cw {f}', and via the marker frequency. This is non-
# destructive (no save), and we restore the original sweep afterward.
# ===========================================================================

def test_probe_cwfreq_units(device):
    # capture the current sweep so we can restore it
    before = _decode(device.command("sweep"))
    print(f"\n  [REPORT] sweep before: {before!r}")

    # set CW to 100000 in whatever unit the device uses
    device.command("cwfreq 100000")
    after_cw = _decode(device.command("cwfreq"))   # bare -> usage string w/ unit
    print(f"  [REPORT] cwfreq usage string: {after_cw!r}")

    # read marker frequency, which reflects the active point in CW
    mk = _decode(device.command("marker"))
    print(f"  [REPORT] marker after cwfreq 100000: {mk!r}")
    print("  [REPORT] INTERPRET: if the reported freq ~= 100000 (Hz) the unit is "
          "Hz; if ~= 100000000 (100 MHz) the unit is kHz.")

    # restore the original sweep if we could parse it (start stop points)
    parts = before.split()
    if len(parts) >= 3 and all(p.lstrip("-").isdigit() for p in parts[:3]):
        device.command(f"sweep {parts[0]} {parts[1]} {parts[2]}")
        print(f"  [REPORT] restored sweep to {parts[0]} {parts[1]} {parts[2]}")
    else:
        print("  [REPORT] could not parse prior sweep to restore; recall a preset "
              "manually if needed")
